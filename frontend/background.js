// Background Service Worker for Chrome Extension

// 追蹤當前請求
let currentController = null;

// 監聽來自 popup 的訊息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'captureScreenshot') {
    captureCurrentTab()
      .then(screenshot => {
        sendResponse({ screenshot });
      })
      .catch(error => {
        console.error('截圖失敗:', error);
        sendResponse({ error: error.message });
      });
    
    return true;
  }
  
  if (request.action === 'sendMessage') {
    handleChatRequest(request.data)
      .then(response => {
        sendResponse({ success: true, response });
      })
      .catch(error => {
        sendResponse({ success: false, error: error.message });
      });
    
    return true;
  }
});

// 截取當前可見的 tab
async function captureCurrentTab() {
  try {
    // 獲取當前活動的 tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab) {
      throw new Error('無法獲取當前標籤頁');
    }
    
    // 檢查是否是受限制的頁面
    const url = tab.url || '';
    if (url.startsWith('chrome://') || url.startsWith('chrome-extension://') || url.startsWith('edge://')) {
      throw new Error('無法截取瀏覽器內部頁面，請在一般網頁使用截圖功能');
    }
    
    // 截取可見區域（使用 JPEG 格式以減小大小）
    const screenshot = await chrome.tabs.captureVisibleTab(null, {
      format: 'jpeg',
      quality: 60  // 進一步降低品質（從 75 降到 60）
    });
    
    console.log('截圖成功，大小:', screenshot.length, '字元');
    
    return screenshot;
  } catch (error) {
    console.error('截圖過程出錯:', error);
    throw error;
  }
}

// 監聽 tab 更新事件（可選：用於清理存儲）
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'loading') {
    // 當網頁開始重新載入時，可以在這裡處理清理邏輯
    console.log(`Tab ${tabId} is reloading`);
  }
});

// 處理聊天請求
async function handleChatRequest(data) {
  const { tabId, message, image, history } = data;
  
  // 如果有進行中的請求，取消它
  if (currentController) {
    console.log('🚫 取消前一個請求');
    currentController.abort();
  }
  
  // 創建新的 AbortController
  currentController = new AbortController();
  
  try {
    // 標記為「處理中」
    await chrome.storage.local.set({
      [`chat_${tabId}_pending`]: {
        status: 'processing',
        userMessage: message,
        timestamp: Date.now()
      }
    });
    
    console.log('📤 發送請求到後端...');
    
    // 發送 API 請求
    const response = await fetch('http://localhost:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, image, history }),
      signal: currentController.signal
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const responseData = await response.json();
    
    console.log('✅ 收到回應');
    
    // 存儲結果
    await chrome.storage.local.set({
      [`chat_${tabId}_pending`]: {
        status: 'completed',
        response: responseData.response,
        timestamp: Date.now()
      }
    });
    
    currentController = null;
    return responseData.response;
    
  } catch (error) {
    if (error.name === 'AbortError') {
      console.log('⏹️  請求被取消');
      // 被新請求取消，不記錄錯誤，但清除 pending 狀態
      await chrome.storage.local.remove(`chat_${tabId}_pending`);
      return null;
    }
    
    console.error('❌ 請求失敗:', error);
    
    // 其他錯誤，記錄下來
    await chrome.storage.local.set({
      [`chat_${tabId}_pending`]: {
        status: 'error',
        error: error.message,
        timestamp: Date.now()
      }
    });
    
    currentController = null;
    throw error;
  }
}

// 安裝事件
chrome.runtime.onInstalled.addListener(() => {
  console.log('AI Website Assistant 已安裝');
});

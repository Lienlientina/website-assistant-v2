// API 配置
const API_BASE_URL = 'http://localhost:8000';

// DOM 元素
const chatContainer = document.getElementById('chatContainer');
const userInput = document.getElementById('userInput');
const sendBtn = document.getElementById('sendBtn');
const screenshotBtn = document.getElementById('screenshotBtn');
const clearHistoryBtn = document.getElementById('clearHistory');
const loadingIndicator = document.getElementById('loadingIndicator');
const screenshotPreview = document.getElementById('screenshotPreview');
const previewImage = document.getElementById('previewImage');
const removeScreenshotBtn = document.getElementById('removeScreenshot');

// 狀態管理
let currentScreenshot = null;
let conversationHistory = [];
let currentTabId = null;
let pollingInterval = null;
let isWaitingForResponse = false; // 追蹤是否正在等待回應

// 初始化
async function init() {
  // 獲取當前 tab ID
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  currentTabId = tab.id;
  
  // 載入歷史記錄
  await loadChatHistory();
  
  // 檢查是否有待處理的請求
  await checkPendingRequest();
  
  // 啟動輪詢檢查
  startPolling();
  
  // 監聽網頁重整事件
  setupTabReloadListener();
}

// 檢查待處理的請求
async function checkPendingRequest() {
  // 如果正在等待回應（剛發送的請求），不要從 storage 讀取
  if (isWaitingForResponse) {
    return;
  }
  
  const result = await chrome.storage.local.get(`chat_${currentTabId}_pending`);
  const pendingData = result[`chat_${currentTabId}_pending`];
  
  if (pendingData) {
    if (pendingData.status === 'processing') {
      console.log('🔄 檢測到進行中的請求');
      // 顯示 loading 狀態
      loadingIndicator.classList.remove('hidden');
      isWaitingForResponse = true; // 標記為等待中
      
    } else if (pendingData.status === 'completed') {
      console.log('✅ 檢測到已完成的請求');
      // 添加回應到 UI
      const assistantMessage = {
        role: 'assistant',
        content: pendingData.response
      };
      conversationHistory.push(assistantMessage);
      addMessageToUI('assistant', assistantMessage.content);
      
      // 儲存並清除 pending 狀態
      await saveChatHistory();
      await chrome.storage.local.remove(`chat_${currentTabId}_pending`);
      loadingIndicator.classList.add('hidden');
      isWaitingForResponse = false;
      
    } else if (pendingData.status === 'error') {
      console.log('❌ 檢測到錯誤的請求');
      // 顯示錯誤
      let errorMsg = pendingData.error;
      if (errorMsg.includes('Failed to fetch')) {
        errorMsg = '無法連接到後端服務。請確認 API 伺服器是否在 http://localhost:8000 運行。';
      }
      addMessageToUI('assistant', `錯誤: ${errorMsg}`);
      
      // 清除 pending 狀態
      await chrome.storage.local.remove(`chat_${currentTabId}_pending`);
      loadingIndicator.classList.add('hidden');
      isWaitingForResponse = false;
    }
  }
}

// 啟動輪詢
function startPolling() {
  // 每 2 秒檢查一次待處理請求
  pollingInterval = setInterval(async () => {
    await checkPendingRequest();
  }, 2000);
}

// 停止輪詢
function stopPolling() {
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }
}

// 載入聊天歷史
async function loadChatHistory() {
  const result = await chrome.storage.local.get([`chat_${currentTabId}`]);
  if (result[`chat_${currentTabId}`]) {
    conversationHistory = result[`chat_${currentTabId}`];
    renderChatHistory();
  }
}

// 儲存聊天歷史
async function saveChatHistory() {
  await chrome.storage.local.set({ [`chat_${currentTabId}`]: conversationHistory });
}

// 渲染聊天歷史
function renderChatHistory() {
  chatContainer.innerHTML = '';
  conversationHistory.forEach(msg => {
    addMessageToUI(msg.role, msg.content, msg.image);
  });
  scrollToBottom();
}

// 添加訊息到 UI
function addMessageToUI(role, content, image = null) {
  const messageDiv = document.createElement('div');
  messageDiv.className = `message ${role}`;
  
  const contentDiv = document.createElement('div');
  contentDiv.className = 'message-content';
  
  if (image && role === 'user') {
    const img = document.createElement('img');
    img.src = image;
    img.className = 'message-image';
    img.alt = '截圖';
    img.onclick = () => openImageInNewTab(image);
    contentDiv.appendChild(img);
  }
  
  const textDiv = document.createElement('div');
  textDiv.textContent = content;
  contentDiv.appendChild(textDiv);
  
  messageDiv.appendChild(contentDiv);
  chatContainer.appendChild(messageDiv);
  scrollToBottom();
}

// 滾動到底部
function scrollToBottom() {
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// 截圖按鈕事件
screenshotBtn.addEventListener('click', async () => {
  try {
    screenshotBtn.disabled = true;
    
    // 通過 background script 截圖
    chrome.runtime.sendMessage({ action: 'captureScreenshot' }, (response) => {
      if (chrome.runtime.lastError) {
        console.error('Chrome runtime error:', chrome.runtime.lastError);
        addMessageToUI('assistant', '截圖失敗：' + chrome.runtime.lastError.message);
        screenshotBtn.disabled = false;
        return;
      }
      
      if (response && response.screenshot) {
        currentScreenshot = response.screenshot;
        previewImage.src = currentScreenshot;
        screenshotPreview.classList.remove('hidden');
        console.log('截圖成功');
      } else if (response && response.error) {
        console.error('截圖錯誤:', response.error);
        addMessageToUI('assistant', '截圖失敗：' + response.error);
      } else {
        console.error('截圖失敗: 未收到回應');
        addMessageToUI('assistant', '截圖失敗，請重試');
      }
      screenshotBtn.disabled = false;
    });
  } catch (error) {
    console.error('截圖錯誤:', error);
    addMessageToUI('assistant', '截圖失敗: ' + error.message);
    screenshotBtn.disabled = false;
  }
});

// 移除截圖按鈕事件
removeScreenshotBtn.addEventListener('click', () => {
  currentScreenshot = null;
  screenshotPreview.classList.add('hidden');
  previewImage.src = '';
});

// 發送按鈕事件
sendBtn.addEventListener('click', sendMessage);

// Enter 鍵發送（Shift+Enter 換行）
userInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
});

// 自動調整 textarea 高度
userInput.addEventListener('input', () => {
  userInput.style.height = 'auto';
  userInput.style.height = userInput.scrollHeight + 'px';
});

// 發送訊息
async function sendMessage() {
  const message = userInput.value.trim();
  
  if (!message && !currentScreenshot) {
    return;
  }
  
  // 如果正在等待回應，表示要取消前一個請求
  if (isWaitingForResponse) {
    console.log('🚫 取消前一個請求，移除未完成的對話');
    // 移除最後一條用戶訊息（未收到回應的）
    if (conversationHistory.length > 0 && conversationHistory[conversationHistory.length - 1].role === 'user') {
      conversationHistory.pop();
      // 重新渲染 UI
      renderChatHistory();
    }
  }
  
  // 保存當前的訊息和截圖
  const messageToSend = message || '(附上截圖)';
  const screenshotToSend = currentScreenshot;
  
  // 立即清空輸入和截圖（在發送前）
  userInput.value = '';
  userInput.style.height = 'auto';
  currentScreenshot = null;
  screenshotPreview.classList.add('hidden');
  
  // 不再禁用輸入（允許用戶繼續輸入）
  // sendBtn.disabled = true;
  // userInput.disabled = true;
  // screenshotBtn.disabled = true;
  
  // 顯示載入指示器
  loadingIndicator.classList.remove('hidden');
  
  // 如果有圖片，顯示特別提示
  if (screenshotToSend) {
    loadingIndicator.querySelector('span').textContent = 'AI 正在分析圖片（圖片處理需較長時間，可發送新訊息取消）';
  } else {
    loadingIndicator.querySelector('span').textContent = 'AI 正在思考中（可發送新訊息取消）';
  }
  
  // 添加用戶訊息到歷史
  const userMessage = {
    role: 'user',
    content: messageToSend,
    image: screenshotToSend
  };
  
  conversationHistory.push(userMessage);
  addMessageToUI('user', userMessage.content, userMessage.image);
  
  // 標記為等待回應
  isWaitingForResponse = true;
  
  // 準備發送的數據
  const requestData = {
    tabId: currentTabId,
    message: messageToSend,
    image: screenshotToSend,
    history: conversationHistory.slice(-6).map(msg => ({
      role: msg.role,
      content: msg.content,
      // 不發送歷史訊息中的圖片，只發送文字
      image: null
    }))
  };
  
  // 通過 background 發送請求
  chrome.runtime.sendMessage({
    action: 'sendMessage',
    data: requestData
  }, async (response) => {
    // 清除等待標記
    isWaitingForResponse = false;
    
    if (chrome.runtime.lastError) {
      console.error('Chrome runtime error:', chrome.runtime.lastError);
      addMessageToUI('assistant', '發送失敗：' + chrome.runtime.lastError.message);
      loadingIndicator.classList.add('hidden');
      return;
    }
    
    if (response && response.success && response.response) {
      // 添加 AI 回應到歷史
      const assistantMessage = {
        role: 'assistant',
        content: response.response
      };
      
      conversationHistory.push(assistantMessage);
      addMessageToUI('assistant', assistantMessage.content);
      
      // 儲存歷史並清除 pending 狀態
      await saveChatHistory();
      await chrome.storage.local.remove(`chat_${currentTabId}_pending`);
      
    } else if (response && !response.success && response.error) {
      // 顯示錯誤
      let errorMsg = response.error;
      if (errorMsg.includes('Failed to fetch')) {
        errorMsg = '無法連接到後端服務。請確認 API 伺服器是否在 http://localhost:8000 運行。';
      }
      addMessageToUI('assistant', `錯誤: ${errorMsg}`);
      await chrome.storage.local.remove(`chat_${currentTabId}_pending`);
    }
    // 如果 response.response 為 null（被取消），不顯示任何訊息
    
    loadingIndicator.classList.add('hidden');
    userInput.focus();
  });
}

// 清除歷史記錄
clearHistoryBtn.addEventListener('click', async () => {
  if (confirm('確定要清除所有對話記錄嗎？')) {
    conversationHistory = [];
    chatContainer.innerHTML = '';
    await chrome.storage.local.remove(`chat_${currentTabId}`);
  }
});

// 監聽 tab 重整
function setupTabReloadListener() {
  chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (tabId === currentTabId && changeInfo.status === 'loading' && tab.url) {
      // 網頁重整時清除該 tab 的歷史記錄
      chrome.storage.local.remove(`chat_${tabId}`).then(() => {
        // 如果當前 popup 還開著，也清空 UI
        if (chatContainer) {
          conversationHistory = [];
          chatContainer.innerHTML = '';
        }
      });
    }
  });
}

// 在新標籤頁中打開圖片
function openImageInNewTab(imageData) {
  const newWindow = window.open();
  newWindow.document.write(`<img src="${imageData}" style="max-width:100%;">`);
}

// 啟動應用
init();

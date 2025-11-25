// Content Script - 注入到網頁中運行
// 目前主要截圖功能由 background.js 處理
// 這個文件保留用於未來可能的頁面交互功能

console.log('AI Website Assistant content script loaded');

// 監聽來自 popup 或 background 的訊息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  // 未來可以在這裡添加頁面相關的功能
  // 例如：選取頁面特定區域、提取頁面文字等
  
  if (request.action === 'getPageContent') {
    // 示例：獲取頁面內容
    const pageContent = {
      title: document.title,
      url: window.location.href,
      text: document.body.innerText.substring(0, 1000) // 限制長度
    };
    sendResponse({ content: pageContent });
  }
  
  return true;
});

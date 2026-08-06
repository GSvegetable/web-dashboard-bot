// 规范化的提示词管理文件
const toastMsg = document.getElementById('toast-message');
const toastBox = document.getElementById('custom-toast');
let toastTimer;

// 使用绝对的数字代号映射你的新提示语
const msgMap = {
    '1': '请输入电报ID',
    '2': '验证码已发送至邮箱',
    '3': '已通过@gsdsjbot向你发送验证码',
    '4': 'ID无效',
    '5': '网络错误',
    '6': '请正确填写所有必填项',
    '7': '表格信息填写不完整',
    '8': '输入密码不一致',
    '9': '验证码错误或已超时',
    '10': '登录成功',
    '11': '注册成功',
    '12': '请求异常'
};

function showToast(id, isError = false) {
    // 根据数字ID获取文字
    const msg = msgMap[id];
    if (!msg) return;

    toastMsg.innerText = msg;

    // 重置样式并应用对应的边框颜色
    toastBox.className = 'toast-glass';
    if (isError) {
        toastBox.classList.add('error');
    } else {
        toastBox.classList.add('success'); // 成功默认挂绿边
    }

    clearTimeout(toastTimer);
    // 触发弹窗入场
    setTimeout(() => { toastBox.classList.add('show'); }, 10);
    
    // 3秒后自动收回
    toastTimer = setTimeout(() => {
        toastBox.classList.remove('show');
    }, 3000);
}

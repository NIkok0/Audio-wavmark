/**
 * 全局通用：加载遮罩与耗时统计
 */

(function() {
    var overlayEl = null;
    var overlayTextEl = null;

    function ensureOverlay() {
        if (overlayEl) return;
        overlayEl = document.createElement('div');
        overlayEl.id = 'global-loading-overlay';
        overlayEl.style.position = 'fixed';
        overlayEl.style.left = '0';
        overlayEl.style.top = '0';
        overlayEl.style.right = '0';
        overlayEl.style.bottom = '0';
        overlayEl.style.background = 'rgba(0,0,0,0.35)';
        overlayEl.style.zIndex = '2000';
        overlayEl.style.display = 'none';
        overlayEl.style.alignItems = 'center';
        overlayEl.style.justifyContent = 'center';

        var inner = document.createElement('div');
        inner.style.background = 'rgba(255,255,255,0.95)';
        inner.style.borderRadius = '10px';
        inner.style.padding = '16px 22px';
        inner.style.boxShadow = '0 4px 16px rgba(0,0,0,0.2)';
        inner.style.display = 'flex';
        inner.style.alignItems = 'center';
        inner.style.gap = '10px';

        var spinner = document.createElement('div');
        spinner.style.width = '18px';
        spinner.style.height = '18px';
        spinner.style.border = '2px solid #ddd';
        spinner.style.borderTopColor = '#0d6efd';
        spinner.style.borderRadius = '50%';
        spinner.style.animation = 'gl-spin 0.9s linear infinite';

        var style = document.createElement('style');
        style.textContent = '@keyframes gl-spin { from { transform: rotate(0); } to { transform: rotate(360deg); } }';
        document.head.appendChild(style);

        overlayTextEl = document.createElement('div');
        overlayTextEl.textContent = '处理中...';
        overlayTextEl.style.color = '#111';
        overlayTextEl.style.fontSize = '14px';

        inner.appendChild(spinner);
        inner.appendChild(overlayTextEl);
        overlayEl.appendChild(inner);
        document.body.appendChild(overlayEl);
    }

    function findPrimaryContainer() {
        return document.querySelector('.watermark-container') || document.querySelector('.container') || document.body;
    }

    function insertAlert(message, type) {
        var container = findPrimaryContainer();
        var wrapper = document.createElement('div');
        wrapper.className = 'alert alert-' + (type || 'info') + ' alert-dismissible fade show';
        wrapper.setAttribute('role', 'alert');
        wrapper.style.marginTop = '10px';
        wrapper.innerHTML = message + '<button type="button" class="close" style="position:absolute; right:10px; top:50%; transform:translateY(-50%); background:none; border:none; font-size:1.5rem; font-weight:700; opacity:.5; padding:0 5px;" aria-label="Close"><span aria-hidden="true">&times;</span></button>';
        container.insertBefore(wrapper, container.firstChild);
        var btn = wrapper.querySelector('.close');
        if (btn) {
            btn.addEventListener('click', function() {
                wrapper.style.opacity = '0';
                setTimeout(function() { wrapper.remove(); }, 300);
            });
        }
        setTimeout(function() {
            if (!wrapper.parentNode) return;
            wrapper.style.opacity = '0';
            setTimeout(function() { wrapper.remove(); }, 500);
        }, 3500);
    }

    window.AppLoading = {
        show: function(message) {
            ensureOverlay();
            overlayTextEl.textContent = message || '处理中...';
            overlayEl.style.display = 'flex';
        },
        hide: function() {
            if (!overlayEl) return;
            overlayEl.style.display = 'none';
        },
        alertInfo: function(message) {
            insertAlert(message, 'info');
        },
        alertSuccess: function(message) {
            insertAlert(message, 'success');
        },
        alertDanger: function(message) {
            insertAlert(message, 'danger');
        }
    };

    // 表单提交：自动显示遮罩并记录开始时间（页面返回后显示耗时）
    document.addEventListener('DOMContentLoaded', function() {
        try {
            var forms = document.querySelectorAll('.watermark-form form, form.needs-loading');
            forms.forEach(function(form) {
                form.addEventListener('submit', function() {
                    try {
                        var key = 'lastActionStart:' + (location.pathname || '');
                        sessionStorage.setItem(key, String(Date.now()));
                    } catch (e) {}
                    AppLoading.show('处理中，请稍候...');
                });
            });

            // 页面返回后，如果存在开始时间则计算并展示耗时
            try {
                var readKey = 'lastActionStart:' + (location.pathname || '');
                var startStr = sessionStorage.getItem(readKey);
                if (startStr) {
                    sessionStorage.removeItem(readKey);
                    var elapsedMs = Date.now() - parseInt(startStr, 10);
                    if (elapsedMs > 0 && elapsedMs < 24 * 60 * 60 * 1000) {
                        var seconds = (elapsedMs / 1000).toFixed(2);
                        AppLoading.alertSuccess('本次操作耗时：' + seconds + ' 秒');
                    }
                }
            } catch (e) {}
        } catch (e) {}
    });
})();

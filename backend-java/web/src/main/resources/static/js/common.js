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
        },
        alertWarning: function(message) {
            insertAlert(message, 'warning');
        }
    };

    // 统一提示方法
    window.showNotification = function(message, type) {
        try {
            switch ((type || 'info').toLowerCase()) {
                case 'success':
                    AppLoading.alertSuccess(message); break;
                case 'danger':
                case 'error':
                    AppLoading.alertDanger(message); break;
                case 'warning':
                    AppLoading.alertWarning(message); break;
                default:
                    AppLoading.alertInfo(message); break;
            }
        } catch (e) {
            // 兜底
            console && console.warn && console.warn('showNotification fallback:', e);
        }
    };

    // 统一确认对话框
    window.showConfirm = function(options) {
        var settings = {
            title: options.title || '确认操作',
            message: options.message || '确定要执行此操作吗？',
            confirmText: options.confirmText || '确定',
            cancelText: options.cancelText || '取消',
            onConfirm: options.onConfirm || function() {},
            onCancel: options.onCancel || function() {},
            type: options.type || 'warning' // warning, danger, info
        };

        // 移除旧的确认框
        var old = document.getElementById('confirmModalBackdrop');
        if (old) old.remove();

        var backdrop = document.createElement('div');
        backdrop.id = 'confirmModalBackdrop';
        backdrop.style.cssText = 'position:fixed;left:0;top:0;right:0;bottom:0;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;';

        var typeConfig = {
            warning: { icon: 'glyphicon-warning-sign', color: '#f0ad4e', btnClass: 'btn-warning' },
            danger: { icon: 'glyphicon-exclamation-sign', color: '#d9534f', btnClass: 'btn-danger' },
            info: { icon: 'glyphicon-info-sign', color: '#5bc0de', btnClass: 'btn-info' }
        };
        var config = typeConfig[settings.type] || typeConfig.warning;

        var modal = document.createElement('div');
        modal.style.cssText = 'background:white;border-radius:12px;box-shadow:0 8px 32px rgba(0,0,0,0.3);min-width:400px;max-width:500px;animation:confirmModalSlide 0.3s ease-out;';

        var style = document.createElement('style');
        style.textContent = '@keyframes confirmModalSlide { from { transform: translateY(-50px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }';
        document.head.appendChild(style);

        modal.innerHTML = `
            <div style="padding:24px;border-bottom:1px solid #e5e5e5;">
                <h4 style="margin:0;color:#333;display:flex;align-items:center;gap:10px;">
                    <i class="glyphicon ${config.icon}" style="color:${config.color};font-size:24px;"></i>
                    <span>${settings.title}</span>
                </h4>
            </div>
            <div style="padding:24px;color:#666;font-size:15px;line-height:1.6;">
                ${settings.message}
            </div>
            <div style="padding:16px 24px;background:#f8f9fa;border-radius:0 0 12px 12px;display:flex;justify-content:flex-end;gap:10px;">
                <button type="button" class="btn btn-default" id="confirmCancelBtn" style="min-width:80px;">
                    ${settings.cancelText}
                </button>
                <button type="button" class="btn ${config.btnClass}" id="confirmOkBtn" style="min-width:80px;">
                    ${settings.confirmText}
                </button>
            </div>
        `;

        backdrop.appendChild(modal);
        document.body.appendChild(backdrop);

        function close() {
            backdrop.style.opacity = '0';
            setTimeout(function() { backdrop.remove(); }, 200);
        }

        document.getElementById('confirmOkBtn').addEventListener('click', function() {
            close();
            settings.onConfirm();
        });

        document.getElementById('confirmCancelBtn').addEventListener('click', function() {
            close();
            settings.onCancel();
        });

        backdrop.addEventListener('click', function(e) {
            if (e.target === backdrop) {
                close();
                settings.onCancel();
            }
        });
    };

    // 页面内联上传：完全匹配 upload 页面风格（手动点击开始上传）
    window.initInlineUploader = function(options) {
        options = options || {};
        var dropZone = document.getElementById(options.dropZoneId);
        if (!dropZone) return;
        
        var fileInput = document.getElementById(options.fileInputId);
        if (!fileInput) return;
        
        var selectBtn = options.selectBtnId ? document.getElementById(options.selectBtnId) : null;
        var uploadUrl = options.uploadUrl;
        if (!uploadUrl) return;
        
        var fileFieldName = options.fileFieldName || 'file';
        var reloadDelay = typeof options.reloadDelay === 'number' ? options.reloadDelay : 2000;

        // 创建上传队列容器（完全匹配 upload.html 结构）
        var queueWrapper = document.createElement('div');
        queueWrapper.className = 'upload-queue';
        queueWrapper.id = options.dropZoneId + '_queue';
        queueWrapper.style.display = 'none';
        queueWrapper.innerHTML = '<h4><i class="glyphicon glyphicon-list"></i> 上传队列</h4><div class="queue-items"></div>';
        
        // 插入到 dropZone 后面
        var parent = dropZone.parentElement;
        if (parent) {
            parent.appendChild(queueWrapper);
        }
        
        var queueItems = queueWrapper.querySelector('.queue-items');
        
        // 获取模板中已存在的"开始上传"按钮（完全匹配 upload.html）
        var uploadBtnId = options.uploadBtnId || (options.dropZoneId.replace('Drop', '') + 'UploadBtn');
        var uploadBtn = document.getElementById(uploadBtnId);
        if (!uploadBtn) {
            console.error('Upload button not found:', uploadBtnId);
            return;
        }

        var uploadQueue = [];

        function addToQueue(filename, status, queueIndex) {
            var item = document.createElement('div');
            item.className = 'queue-item ' + status;
            item.setAttribute('data-queue-index', queueIndex);
            
            var deleteBtn = '<button class="btn btn-xs btn-danger queue-delete-btn" onclick="window.removeFromQueue(\'' + 
                options.dropZoneId + '\', ' + queueIndex + ')" title="删除"><i class="glyphicon glyphicon-remove"></i></button>';
            
            item.innerHTML = '<span class="filename">' + escapeHtml(filename) + '</span>' +
                '<span class="status">' + getStatusText(status) + '</span>' +
                deleteBtn;
            queueItems.appendChild(item);
        }

        function escapeHtml(text) {
            var div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function getStatusText(status) {
            switch(status) {
                case 'pending': return '等待上传';
                case 'uploading': return '上传中...';
                case 'success': return '上传成功';
                case 'error': return '上传失败';
                default: return '';
            }
        }

        function updateQueueItem(index, status) {
            var items = queueItems.children;
            if (items[index]) {
                items[index].className = 'queue-item ' + status;
                var statusSpan = items[index].querySelector('.status');
                if (statusSpan) {
                    statusSpan.textContent = getStatusText(status);
                }
            }
        }

        function handleFiles(files) {
            if (!files || files.length === 0) return;
            
            // 显示队列容器（不清空已有队列）
            queueWrapper.style.display = 'block';
            
            // 添加新文件到队列（追加而不是替换）
            for (var i = 0; i < files.length; i++) {
                var file = files[i];
                var queueIndex = uploadQueue.length; // 使用当前队列长度作为索引
                uploadQueue.push({
                    file: file,
                    status: 'pending',
                    progress: 0
                });
                addToQueue(file.name, 'pending', queueIndex);
            }
            
            // 显示上传按钮
            uploadBtn.style.display = 'inline-block';
        }
        
        // 删除队列中的文件
        function removeFromQueue(queueIndex) {
            if (queueIndex < 0 || queueIndex >= uploadQueue.length) return;
            
            // 从队列数组中移除
            uploadQueue[queueIndex] = null; // 标记为删除（保持索引不变）
            
            // 从 DOM 中移除对应的队列项
            var items = queueItems.querySelectorAll('.queue-item');
            for (var i = 0; i < items.length; i++) {
                if (items[i].getAttribute('data-queue-index') == queueIndex) {
                    items[i].remove();
                    break;
                }
            }
            
            // 如果队列为空，隐藏容器和按钮
            var remainingItems = uploadQueue.filter(function(item) { return item !== null; });
            if (remainingItems.length === 0) {
                queueWrapper.style.display = 'none';
                uploadBtn.style.display = 'none';
            }
        }
        
        // 将删除函数暴露到全局（按 dropZoneId 区分）
        if (!window.queueManagers) {
            window.queueManagers = {};
        }
        window.queueManagers[options.dropZoneId] = {
            removeFromQueue: removeFromQueue
        };
        
        // 全局删除函数
        window.removeFromQueue = function(dropZoneId, queueIndex) {
            if (window.queueManagers[dropZoneId]) {
                window.queueManagers[dropZoneId].removeFromQueue(queueIndex);
            }
        };

        function uploadSelectedFiles() {
            // 过滤掉已删除和已上传的文件
            var filesToUpload = uploadQueue.filter(function(item) {
                return item !== null && item.status === 'pending';
            });
            
            if (filesToUpload.length === 0) {
                alert('没有待上传的文件');
                return;
            }
            
            uploadBtn.disabled = true;
            uploadBtn.innerHTML = '<i class="glyphicon glyphicon-refresh"></i> 上传中...';
            
            // 只上传状态为 pending 的文件
            uploadQueue.forEach(function(item, index) {
                if (item !== null && item.status === 'pending') {
                    uploadFile(item.file, index);
                }
            });
        }

        function uploadFile(file, index) {
            var formData = new FormData();
            formData.append(fileFieldName, file);
            
            var xhr = new XMLHttpRequest();
            xhr.open('POST', uploadUrl, true);
            
            // 更新队列状态
            uploadQueue[index].status = 'uploading';
            updateQueueItem(index, 'uploading');
            
            xhr.upload.onprogress = function(e) {
                if (e.lengthComputable) {
                    var percentComplete = (e.loaded / e.total) * 100;
                    uploadQueue[index].progress = percentComplete;
                }
            };
            
            xhr.onload = function() {
                try {
                    var response = JSON.parse(xhr.responseText);
                    if (xhr.status === 200 && response.success) {
                        uploadQueue[index].status = 'success';
                        updateQueueItem(index, 'success');
                    } else {
                        uploadQueue[index].status = 'error';
                        updateQueueItem(index, 'error');
                    }
                } catch(e) {
                    uploadQueue[index].status = 'error';
                    updateQueueItem(index, 'error');
                }
                
                // 检查是否所有待上传的文件都上传完成
                var allCompleted = uploadQueue.every(function(item) {
                    return item === null || item.status === 'success' || item.status === 'error';
                });
                
                if (allCompleted) {
                    // 恢复上传按钮状态
                    uploadBtn.disabled = false;
                    uploadBtn.innerHTML = '开始上传';
                    
                    // 延迟刷新页面
                    setTimeout(function() {
                        window.location.reload();
                    }, reloadDelay);
                }
            };
            
            xhr.onerror = function() {
                uploadQueue[index].status = 'error';
                updateQueueItem(index, 'error');
            };
            
            xhr.send(formData);
        }

        // 事件绑定
        if (selectBtn) {
            selectBtn.addEventListener('click', function(e) {
                e.preventDefault();
                fileInput.click();
            });
        }

        dropZone.addEventListener('click', function(e) {
            var target = e.target;
            if (target && target.closest && target.closest('.btn')) {
                return;
            }
            fileInput.click();
        });

        ['dragenter', 'dragover'].forEach(function(evt) {
            dropZone.addEventListener(evt, function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.style.borderColor = '#3498db';
            });
        });

        ['dragleave', 'drop'].forEach(function(evt) {
            dropZone.addEventListener(evt, function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropZone.style.borderColor = '';
            });
        });

        dropZone.addEventListener('drop', function(e) {
            var files = Array.from(e.dataTransfer.files || []);
            handleFiles(files);
        });

        fileInput.addEventListener('change', function() {
            handleFiles(Array.from(this.files || []));
        });

        uploadBtn.addEventListener('click', uploadSelectedFiles);
    };

    // 表单提交：自动显示遮罩并记录开始时间（页面返回后显示耗时）
    document.addEventListener('DOMContentLoaded', function() {
        try {
            var forms = document.querySelectorAll('.watermark-form form, form.needs-loading');
            forms.forEach(function(form) {
                form.addEventListener('submit', function(e) {
                    try {
                        if (e && e.defaultPrevented) {
                            return; // 前端验证已阻止，不显示“处理中”
                        }
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

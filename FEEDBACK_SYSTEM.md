# 问题反馈系统说明

## 功能概述

已成功在数字水印系统中添加了问题反馈功能，包括：

1. **主页底部反馈入口**：显示联系方式和反馈入口按钮
2. **独立反馈页面**：用户可以填写详细的问题信息
3. **表单验证**：确保必填字段填写完整
4. **临时存储**：当前版本不保存到数据库（演示模式）

## 文件结构

### 新增文件
- `watermark/templates/feedback.html` - 问题反馈页面模板

### 修改文件
- `watermark/templates/index.html` - 添加了底部反馈区域
- `watermark/views.py` - 添加了两个路由：
  - `/feedback` - 显示反馈页面
  - `/submit_feedback` - 处理表单提交

## 访问路径

- **反馈页面**：`http://localhost:5000/feedback`
- **从主页访问**：滚动到页面底部，点击"提交问题反馈"按钮

## 反馈表单字段

1. **您的姓名** (必填)
2. **联系方式** (必填) - 电话或邮箱
3. **问题类型** (必填) - 下拉选择
   - 功能异常
   - 性能问题
   - 操作疑问
   - 功能建议
   - 其他问题
4. **问题标题** (必填)
5. **详细描述** (必填)

## 联系方式显示

在主页底部和反馈页面都显示了以下联系方式：
- **客服电话**：028-12345678
- **电子邮箱**：support@watermark.com
- **服务时间**：周一至周五 9:00-18:00

## 当前功能特点

### ✅ 已实现
- 美观的响应式界面设计
- 完整的表单验证
- 用户友好的提示信息
- 平滑的动画效果
- 移动端适配

### 📝 演示模式
- 提交后显示弹窗确认（包含提交的信息）
- 信息记录到服务器日志
- **不保存到数据库**
- 提交后自动返回首页

## 如果需要保存到数据库

如果将来需要保存反馈到数据库，需要：

1. 创建 Feedback 模型（在 models.py 中）：
```python
class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(200), nullable=False)
    issue_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, processing, resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
```

2. 修改 submit_feedback 路由（在 views.py 中）：
```python
@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    name = request.form.get('name', '')
    contact = request.form.get('contact', '')
    issue_type = request.form.get('issue_type', '')
    title = request.form.get('title', '')
    description = request.form.get('description', '')
    
    # 创建反馈记录
    feedback = Feedback(
        name=name,
        contact=contact,
        issue_type=issue_type,
        title=title,
        description=description,
        user_id=current_user.id if current_user.is_authenticated else None
    )
    
    db.session.add(feedback)
    db.session.commit()
    
    flash('感谢您的反馈！我们已收到您的问题，会尽快处理。', 'success')
    return redirect(url_for('index'))
```

3. 运行数据库迁移：
```bash
flask db migrate -m "Add feedback table"
flask db upgrade
```

## 样式特点

- 使用渐变色背景和卡片式设计
- 响应式布局，适配各种屏幕尺寸
- 平滑的动画效果
- 统一的设计语言与系统其他页面保持一致

## 测试建议

1. 访问主页，滚动到底部查看反馈入口
2. 点击"提交问题反馈"按钮
3. 填写表单（测试必填字段验证）
4. 提交后查看弹窗信息
5. 验证返回首页功能
6. 测试移动端响应式效果

## 注意事项

- 当前为演示版本，**不会保存到数据库**
- 提交的信息会记录到服务器日志
- 如需启用数据库存储，请参考上述说明进行修改
- 联系方式（电话、邮箱）为示例数据，请根据实际情况修改

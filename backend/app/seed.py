"""初始化演示数据: 三个角色账号 + 内置隐私合规知识库样本。"""

from sqlalchemy.orm import Session

from .auth import hash_password
from .models import Document, User

DEMO_USERS = [
    ("pm", "pm123", "pm"),
    ("qa", "qa123", "qa"),
    ("legal", "legal123", "legal"),
]

KNOWLEDGE_SAMPLES = [
    (
        "个人信息收集最小必要原则.md",
        "根据《个人信息保护法》, 处理个人信息应遵循最小必要原则: 收集个人信息应限于实现处理目的的"
        "最小范围, 不得过度收集。收集前应向用户明示收集的目的、方式和范围, 并取得用户的明示同意。"
        "不得以默认勾选等方式获取同意。收集敏感个人信息(如身份证号、生物识别、金融账户、行踪轨迹)"
        "需取得单独同意并具有特定目的和充分必要性。",
    ),
    (
        "敏感个人信息处理规范.md",
        "敏感个人信息包括生物识别、宗教信仰、特定身份、医疗健康、金融账户、行踪轨迹以及不满十四周岁"
        "未成年人的个人信息。处理敏感个人信息应当取得个人的单独同意, 采取加密、去标识化等安全技术措施, "
        "存储和传输过程必须加密, 并进行严格的访问控制与操作审计。",
    ),
    (
        "数据存储与传输安全要求.md",
        "个人信息的存储应设置合理的保存期限, 到期应删除或匿名化。数据传输应使用 TLS 等加密通道。"
        "敏感字段应加密存储。应建立完整的访问日志与审计机制, 防止越权访问和数据泄露。"
        "第三方 SDK 涉及个人信息外发时应明确告知并取得同意。",
    ),
    (
        "隐私政策与用户协议撰写指引.md",
        "隐私政策应清晰、完整地说明个人信息的收集类型、使用目的、共享对象、存储期限、用户权利"
        "(查阅、更正、删除、撤回同意)及行使方式。用户协议不得包含免除自身责任、加重用户责任、"
        "排除用户主要权利的不公平条款。政策更新应显著提示用户。",
    ),
]


def seed(db: Session) -> None:
    if db.query(User).count() == 0:
        for username, pwd, role in DEMO_USERS:
            db.add(
                User(username=username, password_hash=hash_password(pwd), role=role)
            )
        db.commit()

    if db.query(Document).filter(Document.kind == "knowledge").count() == 0:
        for filename, content in KNOWLEDGE_SAMPLES:
            doc = Document(
                owner_id=None,
                filename=filename,
                mime="text/markdown",
                storage_path="",
                kind="knowledge",
                parse_status="done",
                summary=content[:200],
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

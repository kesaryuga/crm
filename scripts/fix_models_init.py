from pathlib import Path

p = Path(r"C:\Users\Yury\XiaomiMiMoProjects\crm\backend\app\models\__init__.py")
t = "from app.models.contract import Contract, ContractAct, ContractItem, Service\n" + \
    Path(p).read_text(encoding="utf-8").split("from app.models.contract import", 1)[-1].split("\n", 1)[-1]
# cleaner rewrite
t = """from app.models.contract import Contract, ContractAct, ContractItem, Service
from app.models.crm import Comment, Contact, Counterparty, SiteObject
from app.models.document import DocumentTemplate, File, GeneratedDocument
from app.models.equipment import Equipment, EquipmentVerification, ProtocolEquipment
from app.models.idempotency import IdempotencyKey
from app.models.protocol import Protocol, ProtocolRow, ProtocolType, Work
from app.models.task import Notification, Task
from app.models.user import AuditLog, Permission, Role, RolePermission, User

__all__ = [
    "AuditLog",
    "Comment",
    "Contact",
    "Contract",
    "ContractAct",
    "ContractItem",
    "Counterparty",
    "DocumentTemplate",
    "Equipment",
    "EquipmentVerification",
    "File",
    "GeneratedDocument",
    "IdempotencyKey",
    "Notification",
    "Permission",
    "Protocol",
    "ProtocolEquipment",
    "ProtocolRow",
    "ProtocolType",
    "Role",
    "RolePermission",
    "Service",
    "SiteObject",
    "Task",
    "User",
    "Work",
]
"""
p.write_text(t, encoding="utf-8")
print("init ok")

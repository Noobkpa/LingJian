"""创建或重置本地管理员：用户名 admin，密码由命令行传入（默认 123456）。"""
from __future__ import annotations

import argparse
import sys

from backend.app.core.security import hash_password
from backend.app.db.session import SessionLocal
from backend.app.models.orm import Role, User


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--username", default="admin")
    p.add_argument("--password", default="123456")
    args = p.parse_args()

    db = SessionLocal()
    try:
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        if admin_role is None:
            print("roles 未初始化：请先启动过一次后端（会写入 RBAC 种子）", file=sys.stderr)
            sys.exit(1)

        u = db.query(User).filter(User.username == args.username).first()
        if u:
            u.hashed_password = hash_password(args.password)
            u.is_active = True
            if admin_role not in u.roles:
                u.roles.append(admin_role)
            db.commit()
            print(f"已重置密码并确保 admin 角色：{args.username}")
        else:
            user = User(username=args.username, email=None, hashed_password=hash_password(args.password))
            user.roles.append(admin_role)
            db.add(user)
            db.commit()
            print(f"已创建管理员：{args.username}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

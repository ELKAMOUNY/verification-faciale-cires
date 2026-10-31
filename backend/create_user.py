"""
Gestion des comptes de connexion.

  python create_user.py add  email@exemple.ma  "Nom Prénom"          # crée un utilisateur
  python create_user.py add  email@exemple.ma  "Nom" --admin         # crée un administrateur
  python create_user.py password  email@exemple.ma                   # change le mot de passe
  python create_user.py list                                         # liste les comptes
"""
import argparse
import getpass
import sqlite3

import auth


def ask_password():
    p1 = getpass.getpass("Mot de passe (8 caractères min.) : ")
    p2 = getpass.getpass("Confirmez : ")
    if p1 != p2:
        raise SystemExit("Les mots de passe ne correspondent pas.")
    return p1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("email"); a.add_argument("name", nargs="?", default="")
    a.add_argument("--admin", action="store_true")
    pw = sub.add_parser("password"); pw.add_argument("email")
    sub.add_parser("list")
    args = ap.parse_args()

    try:
        if args.cmd == "add":
            auth.create_user(args.email, ask_password(), args.name, "admin" if args.admin else "user")
            print("Compte créé :", args.email)
        elif args.cmd == "password":
            auth.set_password(args.email, ask_password())
            print("Mot de passe modifié pour", args.email)
        else:
            auth.ensure_admin()
            for u in auth.list_users():
                print(f"{u['id']:3d}  {u['email']:35s} {u['role']:6s} {u['name']}")
    except sqlite3.IntegrityError:
        raise SystemExit("Cet e-mail existe déjà.")
    except ValueError as e:
        raise SystemExit(str(e))

import os
import paramiko  # Permet de se connecter à distance via SSH

# Infos de connexion pour l'instance AWS
AWS_HOST = "ec2-user@IP_AWS"               # Remplace IP_AWS par l'adresse de ton serveur AWS
AWS_KEY_PATH = "/chemin/vers/aws-key.pem"  # Chemin vers la clé privée pour accéder à AWS

# Infos de connexion pour la machine bare-metal
BAREMETAL_HOST = "root@IP_BAREMETAL"               # Remplace IP_BAREMETAL par l'adresse de ta machine physique
BAREMETAL_KEY_PATH = "/chemin/vers/baremetal-key.pem"  # Clé privée pour se connecter à la machine bare-metal

# Emplacements des fichiers/projets
REMOTE_ANSIBLE_PATH = "/home/ec2-user/ansible-project"  # Dossier Ansible sur AWS
LOCAL_TEMP_PATH = "/tmp/ansible-project"                # Dossier temporaire local
TARGET_PATH_ON_BAREMETAL = "/opt/ansible-project"       # Où le projet sera copié sur la bare-metal

# Connexion SSH à distance (utilisé pour exécuter des commandes)
def ssh_connect(hostname, key_path):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Accepte automatiquement la clé SSH
    client.connect(
        hostname=hostname.split('@')[-1],   # Récupère l’adresse IP
        username=hostname.split('@')[0],    # Récupère le nom d'utilisateur
        key_filename=key_path               # Utilise la clé privée
    )
    return client  # Retourne la connexion

# Télécharge le projet Ansible depuis AWS vers l’ordinateur local
def download_from_aws():
    os.makedirs(LOCAL_TEMP_PATH, exist_ok=True)
    print("Téléchargement du projet depuis AWS...")
    os.system(f"scp -i {AWS_KEY_PATH} -r {AWS_HOST}:{REMOTE_ANSIBLE_PATH} {LOCAL_TEMP_PATH}")

# Envoie le projet depuis l’ordinateur local vers la machine bare-metal
def upload_to_baremetal():
    print("Envoi du projet vers la machine bare-metal...")
    os.system(f"scp -i {BAREMETAL_KEY_PATH} -r {LOCAL_TEMP_PATH}/ansible-project {BAREMETAL_HOST}:{TARGET_PATH_ON_BAREMETAL}")

# Met à jour le fichier d’inventaire pour que Ansible sache où agir
def update_inventory_file():
    print("Mise à jour de l’inventaire Ansible...")
    inventory_path = os.path.join(LOCAL_TEMP_PATH, "ansible-project", "inventory.ini")
    with open(inventory_path, "w") as f:
        f.write("[baremetal]\n")  # Nom du groupe de serveurs
        f.write("IP_BAREMETAL ansible_user=root ansible_ssh_private_key_file=/chemin/vers/baremetal-key.pem\n")  # Ligne à adapter

# Depuis la machine bare-metal, on vérifie que Ansible peut se connecter
def test_connection_from_baremetal():
    print("Test de connexion avec Ansible...")
    command = f"ansible -i {TARGET_PATH_ON_BAREMETAL}/inventory.ini all -m ping"
    ssh = ssh_connect(BAREMETAL_HOST, BAREMETAL_KEY_PATH)
    stdin, stdout, stderr = ssh.exec_command(command)
    print(stdout.read().decode())  # Résultat du test
    print(stderr.read().decode())  # S'il y a une erreur
    ssh.close()

# Lancement des étapes une par une
def main():
    download_from_aws()              # Étape 1 : Télécharger depuis AWS
    update_inventory_file()          # Étape 2 : Modifier l'inventaire Ansible
    upload_to_baremetal()            # Étape 3 : Envoyer vers la machine bare-metal
    test_connection_from_baremetal()# Étape 4 : Tester la connexion Ansible
    print("✅ Migration terminée avec succès.")

# Point de départ du script
if __name__ == "__main__":
    main()

////

#!/bin/bash

export AWS_KEY=~/.ssh/aws.pem
export BM_KEY=~/.ssh/baremetal.pem
export AWS_HOST=ec2-user@13.48.100.21
export BM_HOST=root@192.168.1.100
export REMOTE_ANSIBLE_PATH=/home/ec2-user/ansible-project
export TARGET_PATH_ON_BM=/opt/ansible-project

python3 migrate_ansible.py

////
chmod +x run_migration.sh
./run_migration.sh
///
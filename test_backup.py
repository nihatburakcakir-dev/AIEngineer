from Source.Core.Backup.backup_manager import BackupManager

backup = BackupManager()

file = r"Assets\Scripts\Managers\BallChainManager.cs"

path = backup.create_backup(file)

print(path)

#!/bin/bash

# Backup SQLite databases
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups/$TIMESTAMP"

mkdir -p $BACKUP_DIR

# Copy database files
cp Back/Data/loan_analysis.db $BACKUP_DIR/
cp Back/loans_vector.db $BACKUP_DIR/

# Backup PDF files
tar -czf $BACKUP_DIR/pdf_backup.tar.gz "Back/PDF Loans/"

echo "Backup completed: $BACKUP_DIR"
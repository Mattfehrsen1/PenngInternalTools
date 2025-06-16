#!/usr/bin/env python3

import os
import sys
from sqlalchemy import text
from database import SessionLocal
from models import Persona, IngestionJob

def main():
    db = SessionLocal()
    
    try:
        print("=== LOCAL PERSONAS WITH COMPLETED FILES ===")
        
        # Get personas with file counts
        result = db.execute(text("""
            SELECT p.id, p.name, p.namespace, p.description, COUNT(ij.id) as file_count
            FROM personas p 
            LEFT JOIN ingestion_jobs ij ON p.id = ij.persona_id 
            WHERE ij.status = 'COMPLETED'
            GROUP BY p.id, p.name, p.namespace, p.description
            HAVING COUNT(ij.id) > 0
            ORDER BY file_count DESC;
        """))
        
        personas = result.fetchall()
        
        if not personas:
            print("No personas found with completed files")
            return
            
        for persona in personas:
            print(f"ID: {persona.id}")
            print(f"Name: {persona.name}")
            print(f"Namespace: {persona.namespace}")
            print(f"Description: {persona.description[:100] + '...' if persona.description and len(persona.description) > 100 else persona.description or 'No description'}")
            print(f"Completed Files: {persona.file_count}")
            print("-" * 60)
            
        # Show total counts
        total_result = db.execute(text("""
            SELECT COUNT(DISTINCT p.id) as persona_count, COUNT(ij.id) as total_files
            FROM personas p 
            LEFT JOIN ingestion_jobs ij ON p.id = ij.persona_id 
            WHERE ij.status = 'COMPLETED'
        """))
        
        totals = total_result.fetchone()
        print(f"\nTOTAL: {totals.persona_count} personas with {totals.total_files} completed files")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    main() 
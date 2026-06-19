import pandas as pd
import sys
import os

excel_path = r"c:\Users\ADMIN\Desktop\Code\Báo Cáo Ads\GA4_Leads_20260429.xlsx"

if not os.path.exists(excel_path):
    print(f"Excel file not found at: {excel_path}")
    sys.exit(1)

try:
    print(f"Reading conversions from {excel_path}...")
    xls = pd.ExcelFile(excel_path)
    print("Sheets in Excel:", xls.sheet_names)
    
    if "Conversions_By_Source" in xls.sheet_names:
        df = pd.read_excel(excel_path, sheet_name="Conversions_By_Source")
        print(f"Successfully loaded Conversions_By_Source sheet with {len(df)} rows.")
        
        # Display some info
        print("\nColumns:", list(df.columns))
        print("\nFirst 5 rows:")
        print(df.head())
        
        # Summary of conversions by Channel_Group
        if "Channel_Group" in df.columns and "Conversions" in df.columns:
            print("\nConversions by Channel Group:")
            print("-" * 50)
            summary_channel = df.groupby("Channel_Group")["Conversions"].sum().sort_values(ascending=False)
            for c, val in summary_channel.items():
                print(f"{c:<30} | Conversions: {val}")
                
        # Summary of conversions by Source / Medium
        if "Source_Medium" in df.columns and "Conversions" in df.columns:
            print("\nConversions by Source / Medium (Top 15):")
            print("-" * 50)
            summary_source = df.groupby("Source_Medium")["Conversions"].sum().sort_values(ascending=False).head(15)
            for s, val in summary_source.items():
                print(f"{s:<30} | Conversions: {val}")
                
        # Summary of conversions by Campaign
        if "Campaign" in df.columns and "Conversions" in df.columns:
            print("\nConversions by Campaign (Top 15):")
            print("-" * 50)
            summary_camp = df.groupby("Campaign")["Conversions"].sum().sort_values(ascending=False).head(15)
            for cp, val in summary_camp.items():
                print(f"{cp:<45} | Conversions: {val}")

        # Total Conversions
        print("\nTotal Conversions in Sheet:", df["Conversions"].sum())
        
    else:
        print("Sheet 'Conversions_By_Source' not found!")
        
    if "All_Events" in xls.sheet_names:
        df_ev = pd.read_excel(excel_path, sheet_name="All_Events")
        print(f"\nLoaded All_Events sheet with {len(df_ev)} rows.")
        if "Event_Name" in df_ev.columns and "Event_Count" in df_ev.columns:
            print("\nEvent counts by Event Name:")
            print("-" * 50)
            ev_summary = df_ev.groupby("Event_Name")["Event_Count"].sum().sort_values(ascending=False)
            for ev, val in ev_summary.items():
                print(f"{ev:<40} | Count: {val}")
                
except Exception as e:
    print("Error reading excel file:", e)

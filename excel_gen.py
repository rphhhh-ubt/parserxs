from datetime import datetime
from io import BytesIO
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font


def create_excel(product_name: str, prices_data: list[dict]) -> bytes:
    """
    Create Excel report with prices for a product.
    
    Args:
        product_name: Name of the product
        prices_data: List of dicts with store, address, and price
                     Example: [{"store": "ТК124", "address": "...", "price": 599.00}]
    
    Returns:
        bytes: Excel file content in XLSX format
    """
    current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
    
    df_data = []
    for item in prices_data:
        df_data.append({
            "Магазин": item["store"],
            "Адрес": item["address"],
            "Цена": item["price"],
            "Дата": current_time
        })
    
    df = pd.DataFrame(df_data)
    
    if not df.empty:
        df = df.sort_values(by="Цена", ascending=True)
    
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=product_name[:31])
        
        workbook = writer.book
        worksheet = writer.sheets[product_name[:31]]
        
        for cell in worksheet[1]:
            cell.font = Font(bold=True)
        
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if cell.value:
                        cell_length = len(str(cell.value))
                        if cell_length > max_length:
                            max_length = cell_length
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
        
        price_col_letter = 'C'
        for row in range(2, len(df) + 2):
            cell = worksheet[f'{price_col_letter}{row}']
            cell.number_format = '0.00'
    
    buffer.seek(0)
    return buffer.read()

from __future__ import annotations
import logging
from datetime import datetime
from autodealer import configure_database
from autodealer.actions.client import get_client_vehicles
from autodealer.services import create_service_order
from datetime import datetime, timedelta

logging.basicConfig(level=logging.DEBUG)

from autodealer.domain import *

configure_database(
    database=r"C:\Program Files (x86)\AutoDealer\AutoDealer\Database\CW.fdb",
    user="SYSDBA",
    password="masterkey",
    host="192.168.88.64",
    port=3050,
    charset="UTF8",
)

if __name__ == "__main__":
    try:
        # Тестов Амаль Тестович
        client = Client.objects.get(client_id=920)    
        cat_1_items = ServiceComplexWorkItem.objects.filter(service_complex_work_tree_id=11).all()
        cat_1_items_ids = [item.service_complex_work_item_id for item in cat_1_items]
        cat_1_works_names = ServiceComplexWork.objects.filter(service_complex_work_item_id__in=cat_1_items_ids).all()
        
        # Папка документов реализации "АвтоМойка"
        document_out_tree_id = 3
        
        now = datetime.now()
        now_finish = now + timedelta(hours=1)
        
        # ИП Кропотов
        organization_id = 1
        
        client_cars = get_client_vehicles(client.client_id) 
        
        doc_id = create_service_order(client_id=client.client_id, 
                                      client_car=client_cars[0].model_link_id,
                                      items=cat_1_works_names, 
                                      document_out_tree_id=document_out_tree_id,
                                      date_start=now,
                                      date_finish=now_finish,
                                      notes="Отладка интеграции с RocketWash", 
                                      service_order_suffix="К",
                                      organization_id=1)        
    except Exception:
        logging.exception("Ошибка")
    finally:
        from autodealer import get_engine

        get_engine().dispose()

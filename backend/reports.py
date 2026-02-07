"""
Генерация отчётов: продажи, остатки.
"""

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend import models


def generate_sales_report(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> dict[str, Any]:
    """
    Отчёт о продажах за период: количество, сумма, прибыль, детализация по моделям.
    Если даты не заданы — учитываются все проданные автомобили.
    """
    q = db.query(models.Car).filter(models.Car.status == "продан")
    if start_date is not None:
        q = q.filter(models.Car.sale_date >= start_date)
    if end_date is not None:
        q = q.filter(models.Car.sale_date <= end_date)

    sold = q.all()

    total_count = len(sold)
    total_sales = sum(c.sale_price or 0 for c in sold)
    total_purchase = sum(c.purchase_price for c in sold)
    total_profit = total_sales - total_purchase
    average_price = total_sales / total_count if total_count else 0.0

    # Период: фактические границы по датам продаж или переданные
    sale_dates = [c.sale_date for c in sold if c.sale_date]
    if sale_dates:
        min_d = min(sale_dates)
        max_d = max(sale_dates)
        period_start = min_d.date() if hasattr(min_d, "date") else min_d
        period_end = max_d.date() if hasattr(max_d, "date") else max_d
    else:
        period_start = start_date.date() if start_date and hasattr(start_date, "date") else None
        period_end = end_date.date() if end_date and hasattr(end_date, "date") else None

    # Детализация по моделям через group_by
    q_agg = db.query(
        models.Car.model,
        func.count(models.Car.id).label("count"),
        func.sum(models.Car.sale_price).label("total"),
        func.sum(models.Car.sale_price - models.Car.purchase_price).label("profit"),
    ).filter(models.Car.status == "продан")
    if start_date is not None:
        q_agg = q_agg.filter(models.Car.sale_date >= start_date)
    if end_date is not None:
        q_agg = q_agg.filter(models.Car.sale_date <= end_date)
    by_model_rows = q_agg.group_by(models.Car.model).all()

    by_model = [
        {
            "model": row.model,
            "count": row.count,
            "total": float(row.total or 0),
            "profit": float(row.profit or 0),
        }
        for row in by_model_rows
    ]

    return {
        "period": {"start": period_start, "end": period_end},
        "total_count": total_count,
        "total_sales": total_sales,
        "total_profit": total_profit,
        "average_price": average_price,
        "by_model": by_model,
    }


def generate_stock_report(db: Session) -> dict[str, Any]:
    """
    Отчёт об остатках на складе: автомобили со статусом != «продан».
    Группировка по моделям и цветам, список автомобилей в каждой группе.
    """
    cars = (
        db.query(models.Car)
        .filter(models.Car.status != "продан")
        .order_by(models.Car.model, models.Car.color, models.Car.vin)
        .all()
    )

    total_count = len(cars)
    total_value = sum(c.purchase_price for c in cars)

    # Группировка: model -> color -> список машин
    by_model: list[dict[str, Any]] = []
    model_map: dict[str, int] = {}  # model -> index в by_model

    for car in cars:
        if car.model not in model_map:
            model_map[car.model] = len(by_model)
            by_model.append({
                "model": car.model,
                "count": 0,
                "value": 0.0,
                "by_color": [],
            })
        mi = model_map[car.model]
        by_model[mi]["count"] += 1
        by_model[mi]["value"] += car.purchase_price

        # Найти или создать группу по цвету
        by_color_list = by_model[mi]["by_color"]
        color_entry = next((e for e in by_color_list if e["color"] == car.color), None)
        if color_entry is None:
            color_entry = {"color": car.color, "count": 0, "cars": []}
            by_color_list.append(color_entry)
        color_entry["count"] += 1
        color_entry["cars"].append({
            "vin": car.vin,
            "purchase_price": car.purchase_price,
            "location": car.location,
        })

    return {
        "total_count": total_count,
        "total_value": total_value,
        "by_model": by_model,
    }


def generate_buyers_report(db: Session) -> dict[str, Any]:
    """
    Отчёт о покупателях и проданных автомобилях: список покупателей,
    для каждого — купленные автомобили с деталями.
    Покупатели отсортированы по сумме покупок (убывание).
    """
    buyers = db.query(models.Buyer).all()
    buyers_data: list[dict[str, Any]] = []

    for buyer in buyers:
        cars = [c for c in buyer.cars if c.status == "продан"]
        total_spent = sum(c.sale_price or 0 for c in cars)
        cars_list = [
            {
                "vin": c.vin,
                "model": c.model,
                "color": c.color,
                "sale_price": c.sale_price or 0,
                "sale_date": c.sale_date.strftime("%Y-%m-%d") if c.sale_date else "",
                "profit": (c.sale_price or 0) - c.purchase_price,
            }
            for c in cars
        ]
        buyers_data.append({
            "name": buyer.name,
            "phone": buyer.phone or "",
            "email": buyer.email or "",
            "purchases_count": len(cars),
            "total_spent": total_spent,
            "cars": cars_list,
        })

    # Сортировка по сумме покупок (от большей к меньшей)
    buyers_data.sort(key=lambda b: b["total_spent"], reverse=True)

    return {
        "total_buyers": len(buyers_data),
        "buyers": buyers_data,
    }

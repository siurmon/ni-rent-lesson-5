import pytest

from src.manager import Manager
from src.models import Parameters, ApartmentSettlement, TenantSettlement
from src.models import Bill


def test_apartment_costs_with_optional_parameters():
    manager = Manager(Parameters())
    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2025-03-15',
        settlement_year=2025,
        settlement_month=2,
        amount_pln=1250.0,
        type='rent'
    ))

    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2024-03-15',
        settlement_year=2024,
        settlement_month=2,
        amount_pln=1150.0,
        type='rent'
    ))

    manager.bills.append(Bill(
        apartment='apart-polanka',
        date_due='2024-02-02',
        settlement_year=2024,
        settlement_month=1,
        amount_pln=222.0,
        type='electricity'
    ))

    costs = manager.get_apartment_costs('apartment-1', 2024, 1)
    assert costs is None

    costs = manager.get_apartment_costs('apart-polanka', 2024, 3)
    assert costs == 0.0

    costs = manager.get_apartment_costs('apart-polanka', 2024, 1)
    assert costs == 222.0

    costs = manager.get_apartment_costs('apart-polanka', 2025, 1)
    assert costs == 910.0
    
    costs = manager.get_apartment_costs('apart-polanka', 2024)
    assert costs == 1372.0

    costs = manager.get_apartment_costs('apart-polanka')
    assert costs == 3532.0

def test_get_apartment_costs():
    parameters = Parameters()
    manager = Manager(parameters)

    # 1. Mieszkanie ma rachunki w tym miesiącu (760.0 + 150.0 = 910.0)
    assert manager.get_apartment_costs('apart-polanka', 2025, 1) == 910.0

    # 2. Mieszkanie istnieje, rok się zgadza, ale w tym miesiącu brak rachunków
    assert manager.get_apartment_costs('apart-polanka', 2025, 2) == 0.0

    # 3. Mieszkanie nie istnieje
    assert manager.get_apartment_costs('non-existent-apartment', 2025, 1) is None

def test_get_apartment_costs_invalid_month():
    parameters = Parameters()
    manager = Manager(parameters)

    with pytest.raises(ValueError):
        manager.get_apartment_costs('apart-polanka', 2025, 13)

    with pytest.raises(ValueError):
        manager.get_apartment_costs('apart-polanka', 2025, 0)

def test_create_apartment_settlement():
    parameters = Parameters()
    manager = Manager(parameters)

    # 1. Mieszkanie ma rachunki w styczniu 2025 (760.0 + 150.0 = 910.0)
    settlement_with_bills = manager.create_apartment_settlement('apart-polanka', 2025, 1)
    assert settlement_with_bills is not None
    assert isinstance(settlement_with_bills, ApartmentSettlement)
    assert settlement_with_bills.apartment == 'apart-polanka'
    assert settlement_with_bills.year == 2025
    assert settlement_with_bills.month == 1
    assert settlement_with_bills.total_rent_pln == 0.0
    assert settlement_with_bills.total_bills_pln == 910.0
    assert settlement_with_bills.total_due_pln == 910.0

    # 2. Mieszkanie nie ma rachunków w lutym 2025
    settlement_no_bills = manager.create_apartment_settlement('apart-polanka', 2025, 2)
    assert settlement_no_bills is not None
    assert isinstance(settlement_no_bills, ApartmentSettlement)
    assert settlement_no_bills.apartment == 'apart-polanka'
    assert settlement_no_bills.total_bills_pln == 0.0
    assert settlement_no_bills.total_due_pln == 0.0

    # 3. Nieistniejące mieszkanie
    assert manager.create_apartment_settlement('non-existent', 2025, 1) is None


def test_create_tenant_settlements():
    parameters = Parameters()
    manager = Manager(parameters)

    # Ustawiamy równe koszty 900.0 PLN dla łatwej weryfikacji podziału
    settlement = ApartmentSettlement(
        apartment='apart-polanka',
        month=1,
        year=2025,
        total_rent_pln=0.0,
        total_bills_pln=900.0,
        total_due_pln=900.0,
    )

    # 1. Mieszkanie ma 3 najemców (2 lub więcej) -> równy podział 900.0 / 3 = 300.0
    tenant_settlements = manager.create_tenant_settlements(settlement)
    assert isinstance(tenant_settlements, list)
    assert len(tenant_settlements) == 3
    for ts in tenant_settlements:
        assert isinstance(ts, TenantSettlement)
        assert ts.apartment_settlement == 'apart-polanka'
        assert ts.year == 2025
        assert ts.month == 1
        assert ts.rent_pln == 0.0
        assert ts.bills_pln == 300.0
        assert ts.total_due_pln == 300.0
        assert ts.balance_pln == -300.0

    # 2. Mieszkanie ma tylko 1 najemcę -> bierze 100% kosztów (900.0)
    manager.tenants = {'tenant-1': manager.tenants['tenant-1']}
    single_tenant_settlements = manager.create_tenant_settlements(settlement)
    assert len(single_tenant_settlements) == 1
    assert single_tenant_settlements[0].tenant == 'tenant-1'
    assert single_tenant_settlements[0].bills_pln == 900.0
    assert single_tenant_settlements[0].total_due_pln == 900.0
    assert single_tenant_settlements[0].balance_pln == -900.0

    # 3. Mieszkanie nie ma żadnych najemców -> nie tworzymy rozliczeń (pusta lista)
    manager.tenants = {}
    empty_settlements = manager.create_tenant_settlements(settlement)
    assert empty_settlements == []

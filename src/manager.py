from src.models import Apartment, ApartmentSettlement, Bill, Parameters, Tenant, TenantSettlement, Transfer


class Manager:
    def __init__(self, parameters: Parameters):
        self.parameters = parameters 

        self.apartments = {}
        self.tenants = {}
        self.transfers = []
        self.bills = []
       
        self.load_data()

    def load_data(self):
        self.apartments = Apartment.from_json_file(self.parameters.apartments_json_path)
        self.tenants = Tenant.from_json_file(self.parameters.tenants_json_path)
        self.transfers = Transfer.from_json_file(self.parameters.transfers_json_path)
        self.bills = Bill.from_json_file(self.parameters.bills_json_path)

    def check_tenants_apartment_keys(self) -> bool:
        for tenant in self.tenants.values():
            if tenant.apartment not in self.apartments:
                return False
        return True

    def get_apartment_costs(
        self,
        apartment_key: str,
        year: int | None = None,
        month: int | None = None,
    ) -> float | None:
        if apartment_key not in self.apartments:
            return None

        if month is not None and not (1 <= month <= 12):
            raise ValueError(f"Invalid month: {month}. Month must be between 1 and 12.")

        total_cost = 0.0
        for bill in self.bills:
            if bill.apartment != apartment_key:
                continue
            if year is not None and bill.settlement_year != year:
                continue
            if month is not None and bill.settlement_month != month:
                continue
            total_cost += bill.amount_pln

        return total_cost

    def create_apartment_settlement(
        self,
        apartment_key: str,
        year: int,
        month: int,
    ) -> ApartmentSettlement | None:
        if apartment_key not in self.apartments:
            return None

        total_bills = self.get_apartment_costs(apartment_key, year, month)
        assert total_bills is not None

        total_rent = 0.0
        total_due = total_rent + total_bills

        return ApartmentSettlement(
            apartment=apartment_key,
            month=month,
            year=year,
            total_rent_pln=total_rent,
            total_bills_pln=total_bills,
            total_due_pln=total_due,
        )

    def create_tenant_settlements(
        self,
        apartment_settlement: ApartmentSettlement,
    ) -> list[TenantSettlement]:
        apartment_tenants = [
            tenant_key
            for tenant_key, tenant in self.tenants.items()
            if tenant.apartment == apartment_settlement.apartment
        ]

        if not apartment_tenants:
            return []

        bills_share = apartment_settlement.total_bills_pln / len(apartment_tenants)

        settlements: list[TenantSettlement] = []
        for tenant_key in apartment_tenants:
            rent_pln = 0.0
            total_due_pln = rent_pln + bills_share
            balance_pln = 0.0 - total_due_pln

            settlements.append(
                TenantSettlement(
                    tenant=tenant_key,
                    apartment_settlement=apartment_settlement.apartment,
                    month=apartment_settlement.month,
                    year=apartment_settlement.year,
                    rent_pln=rent_pln,
                    bills_pln=bills_share,
                    total_due_pln=total_due_pln,
                    balance_pln=balance_pln,
                )
            )

        return settlements
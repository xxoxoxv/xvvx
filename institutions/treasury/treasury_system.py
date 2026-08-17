"""
نظام الخزينة الفدرالية - Federal Treasury System
إدارة المالية العامة، الميزانية، الضرائب، والإنفاق الحكومي
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import json
from enum import Enum


class TransactionType(Enum):
    """أنواع المعاملات المالية"""
    TAX_REVENUE = "tax_revenue"
    OIL_REVENUE = "oil_revenue"
    CUSTOMS_REVENUE = "customs_revenue"
    GOVT_EXPENDITURE = "govt_expenditure"
    SALARY_PAYMENT = "salary_payment"
    PROJECT_FUNDING = "project_funding"
    DEBT_ISSUANCE = "debt_issuance"
    DEBT_REPAYMENT = "debt_repayment"
    TRANSFER = "transfer"


class BudgetCategory(Enum):
    """فئات الميزانية"""
    DEFENSE = "defense"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    INFRASTRUCTURE = "infrastructure"
    SOCIAL_WELFARE = "social_welfare"
    SECURITY = "security"
    ADMINISTRATION = "administration"
    RESEARCH = "research"


class GovernmentAccount:
    """حساب حكومي"""
    
    def __init__(self, account_id: str, name: str, category: str, ministry: str = None):
        self.account_id = account_id
        self.name = name
        self.category = category
        self.ministry = ministry
        self.balance = 0.0
        self.currency = "SAR"
        self.created_at = datetime.now()
        self.transactions: List[Dict] = []
    
    def deposit(self, amount: float, description: str, transaction_type: TransactionType):
        """إيداع مبلغ"""
        if amount <= 0:
            raise ValueError("المبلغ يجب أن يكون موجباً")
        
        self.balance += amount
        transaction = {
            "id": str(uuid.uuid4()),
            "type": transaction_type.value,
            "amount": amount,
            "direction": "credit",
            "description": description,
            "timestamp": datetime.now(),
            "balance_after": self.balance
        }
        self.transactions.append(transaction)
        return transaction
    
    def withdraw(self, amount: float, description: str, transaction_type: TransactionType):
        """سحب مبلغ"""
        if amount <= 0:
            raise ValueError("المبلغ يجب أن يكون موجباً")
        if amount > self.balance:
            raise ValueError("الرصيد غير كافي")
        
        self.balance -= amount
        transaction = {
            "id": str(uuid.uuid4()),
            "type": transaction_type.value,
            "amount": amount,
            "direction": "debit",
            "description": description,
            "timestamp": datetime.now(),
            "balance_after": self.balance
        }
        self.transactions.append(transaction)
        return transaction
    
    def get_statement(self, from_date: datetime = None, to_date: datetime = None) -> List[Dict]:
        """كشف حساب"""
        transactions = self.transactions
        if from_date:
            transactions = [t for t in transactions if t["timestamp"] >= from_date]
        if to_date:
            transactions = [t for t in transactions if t["timestamp"] <= to_date]
        return transactions


class TaxSystem:
    """نظام الضرائب الفدرالي"""
    
    def __init__(self):
        self.tax_rates = {
            "corporate": 0.20,  # 20% ضريبة شركات
            "vat": 0.15,  # 15% ضريبة قيمة مضافة
            "income": {  # ضريبة دخل تصاعدية
                "brackets": [
                    {"min": 0, "max": 60000, "rate": 0.0},
                    {"min": 60000, "max": 120000, "rate": 0.10},
                    {"min": 120000, "max": 240000, "rate": 0.20},
                    {"min": 240000, "max": 500000, "rate": 0.30},
                    {"min": 500000, "max": float('inf'), "rate": 0.35}
                ]
            },
            "customs": 0.05  # 5% رسوم جمركية
        }
        self.tax_records: Dict[str, Dict] = {}
    
    def calculate_income_tax(self, annual_income: float) -> float:
        """حساب ضريبة الدخل التصاعدية"""
        tax = 0.0
        remaining_income = annual_income
        
        brackets = self.tax_rates["income"]["brackets"]
        prev_max = 0
        
        for bracket in brackets:
            if remaining_income <= 0:
                break
            
            bracket_min = bracket["min"]
            bracket_max = bracket["max"]
            rate = bracket["rate"]
            
            taxable_in_bracket = min(remaining_income, bracket_max - prev_max)
            if bracket_max == float('inf'):
                taxable_in_bracket = remaining_income
            
            tax += taxable_in_bracket * rate
            remaining_income -= taxable_in_bracket
            prev_max = bracket_max
        
        return tax
    
    def calculate_vat(self, amount: float) -> float:
        """حساب ضريبة القيمة المضافة"""
        return amount * self.tax_rates["vat"]
    
    def calculate_corporate_tax(self, profit: float) -> float:
        """حساب ضريبة الشركات"""
        return profit * self.tax_rates["corporate"]
    
    def file_tax_return(self, taxpayer_id: str, tax_type: str, amount: float, period: str):
        """تقديم إقرار ضريبي"""
        if taxpayer_id not in self.tax_records:
            self.tax_records[taxpayer_id] = {"returns": []}
        
        tax_return = {
            "id": str(uuid.uuid4()),
            "taxpayer_id": taxpayer_id,
            "tax_type": tax_type,
            "amount": amount,
            "period": period,
            "filed_at": datetime.now(),
            "status": "filed"
        }
        
        self.tax_records[taxpayer_id]["returns"].append(tax_return)
        return tax_return


class FederalBudget:
    """الميزانية الفدرالية السنوية"""
    
    def __init__(self, year: int):
        self.year = year
        self.total_revenue = 0.0
        self.total_expenditure = 0.0
        self.categories: Dict[BudgetCategory, float] = {cat: 0.0 for cat in BudgetCategory}
        self.allocations: Dict[str, float] = {}
        self.status = "draft"  # draft, approved, executing, closed
        self.approval_date: Optional[datetime] = None
    
    def allocate(self, category: BudgetCategory, amount: float, recipient: str):
        """تخصيص مبلغ لفئة معينة"""
        if self.status not in ["draft", "approved"]:
            raise Exception("لا يمكن التعديل على ميزانية مغلقة أو قيد التنفيذ")
        
        self.categories[category] += amount
        if recipient not in self.allocations:
            self.allocations[recipient] = 0.0
        self.allocations[recipient] += amount
    
    def approve(self):
        """اعتماد الميزانية"""
        if self.status != "draft":
            raise Exception("الميزانية ليست في حالة مسودة")
        self.status = "approved"
        self.approval_date = datetime.now()
    
    def get_balance(self) -> float:
        """حساب الرصيد (فائض/عجز)"""
        return self.total_revenue - self.total_expenditure
    
    def get_surplus_deficit(self) -> str:
        """تحديد الفائض أو العجز"""
        balance = self.get_balance()
        if balance > 0:
            return f"فائض: {balance:,.2f} SAR"
        elif balance < 0:
            return f"عجز: {abs(balance):,.2f} SAR"
        else:
            return "متوازن"


class FederalTreasury:
    """الخزينة الفدرالية - الهيئة الرئيسية"""
    
    def __init__(self):
        self.accounts: Dict[str, GovernmentAccount] = {}
        self.budgets: Dict[int, FederalBudget] = {}
        self.tax_system = TaxSystem()
        self.total_reserves = 0.0
        self.public_debt = 0.0
        self.transactions: List[Dict] = []
        
        # إنشاء الحسابات الرئيسية
        self._initialize_accounts()
    
    def _initialize_accounts(self):
        """تهيئة الحسابات الحكومية الرئيسية"""
        # الحساب العام للخزينة
        self.create_account("TREASURY-MAIN", "الحساب العام للخزينة الفدرالية", "treasury")
        
        # حسابات الوزارات
        ministries = [
            ("MIN-DEF", "وزارة الدفاع", "defense", "defense"),
            ("MIN-EDU", "وزارة التعليم", "education", "education"),
            ("MIN-HEALTH", "وزارة الصحة", "healthcare", "healthcare"),
            ("MIN-INFRA", "وزارة البنية التحتية", "infrastructure", "infrastructure"),
            ("MIN-SOCIAL", "وزارة الشؤون الاجتماعية", "social_welfare", "social_welfare"),
            ("MIN-INT", "وزارة الداخلية", "security", "security"),
        ]
        
        for acc_id, name, category, ministry in ministries:
            self.create_account(acc_id, name, category, ministry)
    
    def create_account(self, account_id: str, name: str, category: str, ministry: str = None) -> GovernmentAccount:
        """إنشاء حساب حكومي جديد"""
        if account_id in self.accounts:
            raise Exception("الحساب موجود مسبقاً")
        
        account = GovernmentAccount(account_id, name, category, ministry)
        self.accounts[account_id] = account
        return account
    
    def collect_tax(self, taxpayer_id: str, amount: float, tax_type: str, period: str):
        """تحصيل ضريبة"""
        # تسجيل الإقرار الضريبي
        self.tax_system.file_tax_return(taxpayer_id, tax_type, amount, period)
        
        # إيداع في الحساب العام
        main_account = self.accounts["TREASURY-MAIN"]
        transaction = main_account.deposit(
            amount,
            f"تحصيل {tax_type} من {taxpayer_id} للفترة {period}",
            TransactionType.TAX_REVENUE
        )
        
        self.total_reserves += amount
        self.transactions.append({
            "type": "tax_collection",
            "taxpayer_id": taxpayer_id,
            "amount": amount,
            "tax_type": tax_type,
            "period": period,
            "transaction_id": transaction["id"],
            "timestamp": datetime.now()
        })
        
        return transaction
    
    def disburse_funds(self, account_id: str, amount: float, purpose: str, category: BudgetCategory):
        """صرف أموال"""
        if account_id not in self.accounts:
            raise Exception("الحساب غير موجود")
        
        account = self.accounts[account_id]
        main_account = self.accounts["TREASURY-MAIN"]
        
        # تحويل من الحساب العام إلى حساب الجهة
        main_account.withdraw(amount, f"صرف لـ {account.name}: {purpose}", TransactionType.GOV_T_EXPENDITURE)
        account.deposit(amount, purpose, TransactionType.GOV_T_EXPENDITURE)
        
        self.transactions.append({
            "type": "disbursement",
            "recipient_account": account_id,
            "amount": amount,
            "purpose": purpose,
            "category": category.value,
            "timestamp": datetime.now()
        })
    
    def create_budget(self, year: int) -> FederalBudget:
        """إنشاء ميزانية سنوية"""
        if year in self.budgets:
            raise Exception("الميزانية موجودة مسبقاً")
        
        budget = FederalBudget(year)
        self.budgets[year] = budget
        return budget
    
    def pay_salaries(self, total_amount: float, period: str):
        """دفع رواتب الموظفين الحكوميين"""
        main_account = self.accounts["TREASURY-MAIN"]
        transaction = main_account.withdraw(
            total_amount,
            f"دفع رواتب الفترة {period}",
            TransactionType.SALARY_PAYMENT
        )
        
        self.transactions.append({
            "type": "salary_payment",
            "amount": total_amount,
            "period": period,
            "transaction_id": transaction["id"],
            "timestamp": datetime.now()
        })
        
        return transaction
    
    def issue_debt(self, amount: float, interest_rate: float, maturity_years: int):
        """إصدار سند دين سيادي"""
        main_account = self.accounts["TREASURY-MAIN"]
        main_account.deposit(
            amount,
            f"إصدار سند دين بقيمة {amount}",
            TransactionType.DEBT_ISSUANCE
        )
        
        self.public_debt += amount
        self.total_reserves += amount
        
        self.transactions.append({
            "type": "debt_issuance",
            "amount": amount,
            "interest_rate": interest_rate,
            "maturity_years": maturity_years,
            "timestamp": datetime.now()
        })
    
    def get_financial_report(self) -> Dict:
        """تقرير مالي شامل"""
        return {
            "total_reserves": self.total_reserves,
            "public_debt": self.public_debt,
            "net_position": self.total_reserves - self.public_debt,
            "total_accounts": len(self.accounts),
            "accounts_summary": {
                acc_id: {"name": acc.name, "balance": acc.balance}
                for acc_id, acc in self.accounts.items()
            },
            "budgets": {
                year: {
                    "revenue": budget.total_revenue,
                    "expenditure": budget.total_expenditure,
                    "balance": budget.get_balance(),
                    "status": budget.status
                }
                for year, budget in self.budgets.items()
            },
            "recent_transactions": self.transactions[-10:] if self.transactions else []
        }


# مثال استخدام
if __name__ == "__main__":
    treasury = FederalTreasury()
    
    # تحصيل ضرائب
    treasury.collect_tax("COMP-001", 1000000, "corporate", "2025-Q1")
    treasury.collect_tax("COMP-002", 500000, "vat", "2025-Q1")
    
    # إنشاء ميزانية 2025
    budget = treasury.create_budget(2025)
    budget.total_revenue = 5000000000  # 5 مليار
    budget.total_expenditure = 4500000000  # 4.5 مليار
    budget.approve()
    
    # صرف أموال للتعليم
    treasury.disburse_funds("MIN-EDU", 100000000, "بناء مدارس جديدة", BudgetCategory.EDUCATION)
    
    # دفع رواتب
    treasury.pay_salaries(50000000, "يناير 2025")
    
    # إصدار دين سيادي
    treasury.issue_debt(2000000000, 0.045, 10)
    
    # تقرير مالي
    report = treasury.get_financial_report()
    print(json.dumps(report, indent=2, default=str, ensure_ascii=False))

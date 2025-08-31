import pytest
from pydantic import ValidationError
from core.validation import (
    validate_xor_fields, validate_sales_input,
    validate_industry, validate_product, validate_stage, validate_purpose
)
from core.models import SalesInput, SalesType

class TestURLValidation:
    """PydanticによるURL検証のテスト"""

    def test_valid_urls(self):
        """有効なURLが受理される"""
        SalesInput(
            sales_type=SalesType.HUNTER,
            industry="IT",
            product="SaaS",
            description_url="https://example.com",
            stage="初期接触",
            purpose="新規顧客獲得"
        )
        SalesInput(
            sales_type=SalesType.HUNTER,
            industry="IT",
            product="SaaS",
            competitor_url="https://competitor.com",
            stage="初期接触",
            purpose="新規顧客獲得"
        )

    def test_invalid_urls(self):
        """無効なURLはValidationErrorを投げる"""
        with pytest.raises(ValidationError):
            SalesInput(
                sales_type=SalesType.HUNTER,
                industry="IT",
                product="SaaS",
                description_url="not-a-url",
                stage="初期接触",
                purpose="新規顧客獲得"
            )

        with pytest.raises(ValidationError):
            SalesInput(
                sales_type=SalesType.HUNTER,
                industry="IT",
                product="SaaS",
                competitor_url="not-a-url",
                stage="初期接触",
                purpose="新規顧客獲得"
            )

class TestXORFieldsValidation:
    """XORフィールド検証のテスト"""
    
    def test_valid_xor_combinations(self):
        """有効なXORフィールドの組み合わせ"""
        # 説明フィールドのテスト
        input1 = SalesInput(
            sales_type=SalesType.HUNTER,
            industry="IT",
            product="SaaS",
            description="商品の説明",
            description_url=None,
            competitor="競合A",
            competitor_url=None,
            stage="初期接触",
            purpose="新規顧客獲得"
        )
        errors = validate_xor_fields(input1)
        assert len(errors) == 0, f"Should have no errors: {errors}"
        
        # 競合フィールドのテスト
        input2 = SalesInput(
            sales_type=SalesType.HUNTER,
            industry="IT",
            product="SaaS",
            description=None,
            description_url="https://example.com",
            competitor=None,
            competitor_url="https://competitor.com",
            stage="初期接触",
            purpose="新規顧客獲得"
        )
        errors = validate_xor_fields(input2)
        assert len(errors) == 0, f"Should have no errors: {errors}"
    
    def test_invalid_xor_combinations(self):
        """無効なXORフィールドの組み合わせ"""
        # 説明フィールドの両方入力
        input1 = SalesInput(
            sales_type=SalesType.HUNTER,
            industry="IT",
            product="SaaS",
            description="商品の説明",
            description_url="https://example.com",
            competitor="競合A",
            competitor_url=None,
            stage="初期接触",
            purpose="新規顧客獲得"
        )
        errors = validate_xor_fields(input1)
        assert len(errors) == 1, f"Should have 1 error: {errors}"
        assert "説明はテキストまたはURLのいずれか一方を入力してください" in errors[0]
        
        # 競合フィールドの両方入力
        input2 = SalesInput(
            sales_type=SalesType.HUNTER,
            industry="IT",
            product="SaaS",
            description="商品の説明",
            description_url=None,
            competitor="競合A",
            competitor_url="https://competitor.com",
            stage="初期接触",
            purpose="新規顧客獲得"
        )
        errors = validate_xor_fields(input2)
        assert len(errors) == 1, f"Should have 1 error: {errors}"
        assert "競合はテキストまたはURLのいずれか一方を入力してください" in errors[0]

class TestFieldValidation:
    """個別フィールド検証のテスト"""
    
    def test_industry_validation(self):
        """業界名の検証テスト"""
        # 有効な業界名
        assert len(validate_industry("IT")) == 0
        assert len(validate_industry("製造業")) == 0
        assert len(validate_industry("金融・保険業")) == 0
        
        # 無効な業界名
        errors = validate_industry("")
        assert len(errors) == 1
        assert "業界は必須です" in errors[0]
        
        errors = validate_industry("A")
        assert len(errors) == 1
        assert "業界は2文字以上で入力してください" in errors[0]
        
        errors = validate_industry("A" * 101)
        assert len(errors) == 1
        assert "業界は100文字以下で入力してください" in errors[0]
        
        errors = validate_industry("IT<script>")
        assert len(errors) == 1
        assert "無効な文字" in errors[0]
    
    def test_product_validation(self):
        """商品・サービス名の検証テスト"""
        # 有効な商品名
        assert len(validate_product("SaaS")) == 0
        assert len(validate_product("コンサルティングサービス")) == 0
        
        # 無効な商品名
        errors = validate_product("")
        assert len(errors) == 1
        assert "商品・サービスは必須です" in errors[0]
        
        errors = validate_product("A")
        assert len(errors) == 1
        assert "商品・サービスは2文字以上で入力してください" in errors[0]
        
        errors = validate_product("A" * 201)
        assert len(errors) == 1
        assert "商品・サービスは200文字以下で入力してください" in errors[0]
    
    def test_stage_validation(self):
        """商談ステージの検証テスト"""
        valid_stages = ["初期接触", "ニーズ発掘", "提案", "商談", "クロージング"]
        for stage in valid_stages:
            assert validate_stage(stage) == True, f"Stage should be valid: {stage}"
        
        assert validate_stage("無効なステージ") == False
        assert validate_stage("") == False
    
    def test_purpose_validation(self):
        """目的の検証テスト"""
        # 有効な目的
        assert len(validate_purpose("新規顧客獲得")) == 0
        assert len(validate_purpose("既存顧客の拡大")) == 0
        
        # 無効な目的
        errors = validate_purpose("")
        assert len(errors) == 1
        assert "目的は必須です" in errors[0]
        
        errors = validate_purpose("拡大")
        assert len(errors) == 1
        assert "目的は5文字以上で入力してください" in errors[0]
        
        errors = validate_purpose("A" * 501)
        assert len(errors) == 1
        assert "目的は500文字以下で入力してください" in errors[0]

class TestSalesInputValidation:
    """SalesInput全体の検証テスト"""
    
    def test_valid_sales_input(self):
        """有効なSalesInputのテスト"""
        input_data = SalesInput(
            sales_type=SalesType.HUNTER,
            industry="IT",
            product="SaaS",
            description="商品の説明",
            description_url=None,
            competitor="競合A",
            competitor_url=None,
            stage="初期接触",
            purpose="新規顧客獲得",
            constraints=["予算制限", "期間制限"]
        )
        
        errors = validate_sales_input(input_data)
        assert len(errors) == 0, f"Should have no errors: {errors}"
    
    def test_invalid_sales_input(self):
        """無効なSalesInputのテスト"""
        # 必須フィールド不足
        input_data = SalesInput(
            sales_type=SalesType.HUNTER,
            industry="",
            product="",
            description=None,
            description_url=None,
            competitor=None,
            competitor_url=None,
            stage="",
            purpose="",
            constraints=[]
        )
        
        errors = validate_sales_input(input_data)
        assert len(errors) > 0, "Should have validation errors"
        
        # 特定のエラーメッセージの確認
        error_messages = [error for error in errors]
        assert any("業界は必須です" in error for error in error_messages)
        assert any("商品・サービスは必須です" in error for error in error_messages)
        assert any("商談ステージは必須です" in error for error in error_messages)
        assert any("目的は必須です" in error for error in error_messages)
    
    def test_constraints_validation(self):
        """制約フィールドの検証テスト"""
        input_data = SalesInput(
            sales_type=SalesType.HUNTER,
            industry="IT",
            product="SaaS",
            description="商品の説明",
            description_url=None,
            competitor="競合A",
            competitor_url=None,
            stage="初期接触",
            purpose="新規顧客獲得",
            constraints=["", "短", "有効な制約"]
        )
        
        errors = validate_sales_input(input_data)
        assert len(errors) > 0, "Should have validation errors"
        
        # 制約のエラーメッセージの確認
        error_messages = [error for error in errors]
        assert any("制約1が空です" in error for error in error_messages)
        assert any("制約2は3文字以上で入力してください" in error for error in error_messages)


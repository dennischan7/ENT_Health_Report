# 中小企业健康度诊断平台财务数据库设计规范

## 一、数据库表命名标准

### 1.1 基础命名规范
- 使用小写英文字符与下划线组合命名（snake_case）
- 表名前缀：`fin_` (Financial缩写)
- 常用后缀：
  - `_stmt`: 报表 (Statement)
  - `_detl`: 明细 (Detail)  
  - `_sum`: 汇总 (Summary)
  - `_his`: 历史 (Historical)

### 1.2 主要财务表名
- 利润表: `fin_income_stmt` (损益表)
- 资产负债表: `fin_balance_stmt` (财务状况表)
- 现金流量表: `fin_cashflow_stmt`

## 二、利润表 (Income Statement) 设计

### 2.1 表结构 `fin_income_stmt`
```sql
CREATE TABLE fin_income_stmt (
  id SERIAL PRIMARY KEY,
  company_code VARCHAR(20) NOT NULL,
  company_name VARCHAR(100) NOT NULL,
  report_period DATE NOT NULL, -- 报告期间
  report_period_type VARCHAR(10) NOT NULL, -- 报告期限类型(月报QTR/季报YTD等)
  currency CHAR(3) DEFAULT 'CNY', -- 货币单位
  
  -- 收入类
  operating_revenue NUMERIC(18,2), -- 营业收入
  interest_income NUMERIC(18,2), -- 利息收入
  investment_income NUMERIC(18,2), -- 投资收益
  
  -- 成本费用类
  operating_cost NUMERIC(18,2), -- 营业成本
  tax_surcharges NUMERIC(18,2), -- 税金及附加
  sale_expense NUMERIC(18,2), -- 销售费用
  manage_expense NUMERIC(18,2), -- 管理费用
  finance_expense NUMERIC(18,2), -- 财务费用
  
  -- 利润类
  operating_profit NUMERIC(18,2), -- 营业利润
  net_profit_before_tax NUMERIC(18,2), -- 利润总额
  income_tax_expense NUMERIC(18,2), -- 所得税费用
  net_profit NUMERIC(18,2), -- 净利润
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  remark TEXT
);

-- 为常用查询字段建立索引
CREATE INDEX idx_fin_income_company_period ON fin_income_stmt(company_code, report_period);
```

### 2.2 添加表和字段注释
```sql
COMMENT ON TABLE fin_income_stmt IS '利润表';
COMMENT ON COLUMN fin_income_stmt.company_code IS '公司代码';
COMMENT ON COLUMN fin_income_stmt.company_name IS '公司名称';
COMMENT ON COLUMN fin_income_stmt.report_period IS '报告期间';
COMMENT ON COLUMN fin_income_stmt.report_period_type IS '报告期间类型(MONTH, QUARTER, YEAR)';
COMMENT ON COLUMN fin_income_stmt.currency IS '货币单位';
COMMENT ON COLUMN fin_income_stmt.operating_revenue IS '营业收入';
COMMENT ON COLUMN fin_income_stmt.interest_income IS '利息收入';
COMMENT ON COLUMN fin_income_stmt.investment_income IS '投资收益';
COMMENT ON COLUMN fin_income_stmt.operating_cost IS '营业成本';
COMMENT ON COLUMN fin_income_stmt.tax_surcharges IS '税金及附加';
COMMENT ON COLUMN fin_income_stmt.sale_expense IS '销售费用';
COMMENT ON COLUMN fin_income_stmt.manage_expense IS '管理费用';
COMMENT ON COLUMN fin_income_stmt.finance_expense IS '财务费用';
COMMENT ON COLUMN fin_income_stmt.operating_profit IS '营业利润';
COMMENT ON COLUMN fin_income_stmt.net_profit_before_tax IS '利润总额';
COMMENT ON COLUMN fin_income_stmt.income_tax_expense IS '所得税费用';
COMMENT ON COLUMN fin_income_stmt.net_profit IS '净利润';
```

## 三、资产负债表 (Balance Sheet) 设计

### 3.1 表结构 `fin_balance_stmt`
```sql
CREATE TABLE fin_balance_stmt (
  id SERIAL PRIMARY KEY,
  company_code VARCHAR(20) NOT NULL,
  company_name VARCHAR(100) NOT NULL,
  report_period DATE NOT NULL,
  report_period_type VARCHAR(10) DEFAULT 'Y',
  currency CHAR(3) DEFAULT 'CNY',
  
  -- 资产类
  cash_equivalents NUMERIC(18,2), -- 货币资金
  deposits_receivable NUMERIC(18,2), -- 存放中央银行款项
  trading_fin_assets NUMERIC(18,2), -- 交易性金融资产
  notes_receivable NUMERIC(18,2), -- 应收票据
  accounts_receivable NUMERIC(18,2), -- 应收账款
  inventory NUMERIC(18,2), -- 存货
  current_assets_total NUMERIC(18,2), -- 流动资产合计
  
  fixed_assets NUMERIC(18,2), -- 固定资产
  construction_in_progress NUMERIC(18,2), -- 在建工程
  intangible_assets NUMERIC(18,2), -- 无形资产
  total_assets NUMERIC(18,2), -- 资产总计
  
  -- 负债类
  short_term_loan NUMERIC(18,2), -- 短期借款
  notes_payable NUMERIC(18,2), -- 应付票据
  accounts_payable NUMERIC(18,2), -- 应付账款
  current_liabilities_total NUMERIC(18,2), -- 流动负债合计
  long_term_loan NUMERIC(18,2), -- 长期借款
  total_liabilities NUMERIC(18,2), -- 负债合计
  
  -- 所有者权益类
  share_capital NUMERIC(18,2), -- 实收资本(或股本)
  capital_reserve NUMERIC(18,2), -- 资本公积
  surplus_reserve NUMERIC(18,2), -- 盈余公积
  undistributed_profits NUMERIC(18,2), -- 未分配利润
  total_owners_equity NUMERIC(18,2), -- 所有者权益合计
  
  -- 平衡检查
  liability_equity_total NUMERIC(18,2), -- 负债和所有者权益总计
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  remark TEXT
);

CREATE INDEX idx_fin_balance_company_period ON fin_balance_stmt(company_code, report_period);
```

### 3.2 添加注释
```sql
COMMENT ON TABLE fin_balance_stmt IS '资产负债表';
COMMENT ON COLUMN fin_balance_stmt.company_code IS '公司代码';
COMMENT ON COLUMN fin_balance_stmt.company_name IS '公司名称';
COMMENT ON COLUMN fin_balance_stmt.report_period IS '报告期截止日';
COMMENT ON COLUMN fin_balance_stmt.currency IS '货币单位';
COMMENT ON COLUMN fin_balance_stmt.cash_equivalents IS '货币资金';
COMMENT ON COLUMN fin_balance_stmt.deposits_receivable IS '存放中央银行款项';
COMMENT ON COLUMN fin_balance_stmt.trading_fin_assets IS '交易性金融资产';
COMMENT ON COLUMN fin_balance_stmt.notes_receivable IS '应收票据';
COMMENT ON COLUMN fin_balance_stmt.accounts_receivable IS '应收账款';
COMMENT ON COLUMN fin_balance_stmt.inventory IS '存货';
COMMENT ON COLUMN fin_balance_stmt.current_assets_total IS '流动资产合计';
COMMENT ON COLUMN fin_balance_stmt.fixed_assets IS '固定资产';
COMMENT ON COLUMN fin_balance_stmt.construction_in_progress IS '在建工程';
COMMENT ON COLUMN fin_balance_stmt.intangible_assets IS '无形资产';
COMMENT ON COLUMN fin_balance_stmt.total_assets IS '资产总计';
COMMENT ON COLUMN fin_balance_stmt.short_term_loan IS '短期借款';
COMMENT ON COLUMN fin_balance_stmt.notes_payable IS '应付票据';
COMMENT ON COLUMN fin_balance_stmt.accounts_payable IS '应付账款';
COMMENT ON COLUMN fin_balance_stmt.current_liabilities_total IS '流动负债合计';
COMMENT ON COLUMN fin_balance_stmt.long_term_loan IS '长期借款';
COMMENT ON COLUMN fin_balance_stmt.total_liabilities IS '负债合计';
COMMENT ON COLUMN fin_balance_stmt.share_capital IS '实收资本(或股本)';
COMMENT ON COLUMN fin_balance_stmt.capital_reserve IS '资本公积';
COMMENT ON COLUMN fin_balance_stmt.surplus_reserve IS '盈余公积';
COMMENT ON COLUMN fin_balance_stmt.undistributed_profits IS '未分配利润';
COMMENT ON COLUMN fin_balance_stmt.total_owners_equity IS '所有者权益合计';
COMMENT ON COLUMN fin_balance_stmt.liability_equity_total IS '负债和所有者权益总计';
```

## 四、现金流量表 (Cash Flow Statement) 设计

### 4.1 表结构 `fin_cashflow_stmt`
```sql
CREATE TABLE fin_cashflow_stmt (
  id SERIAL PRIMARY KEY,
  company_code VARCHAR(20) NOT NULL,
  company_name VARCHAR(100) NOT NULL,
  report_period DATE NOT NULL,
  report_period_type VARCHAR(10) DEFAULT 'Y',
  currency CHAR(3) DEFAULT 'CNY',
  
  -- 经营活动现金流量
  cfo_sales_service NUMERIC(18,2), -- 销售商品、提供劳务收到的现金
  cfo_receivables NUMERIC(18,2), -- 收到的税费返还
  cfo_other_operating NUMERIC(18,2), -- 收到其他与经营活动有关的现金
  cfo_subtotal_in NUMERIC(18,2), -- 经营活动现金流入小计
  cfo_goods_services NUMERIC(18,2), -- 购买商品、接受劳务支付的现金
  cfo_employee_payments NUMERIC(18,2), -- 支付给职工以及为职工支付的现金
  cfo_payments_to_suppliers NUMERIC(18,2), -- 支付的各项税费
  cfo_other_out NUMERIC(18,2), -- 支付其他与经营活动有关的现金
  cfo_net_operating NUMERIC(18,2), -- 经营活动产生的现金流量净额
  
  -- 投资活动现金流量
  cfi_acquire_fixed NUMERIC(18,2), -- 购建固定资产、无形资产和其他长期资产支付的现金
  cfi_dispose_fixed NUMERIC(18,2), -- 处置固定资产、无形资产和其他长期资产收回的现金净额
  cfi_invest NUMERIC(18,2), -- 投资支付的现金
  cfi_dividend_interest NUMERIC(18,2), -- 取得投资收益收到的现金
  cfi_net_investing NUMERIC(18,2), -- 投资活动产生的现金流量净额
  
  -- 筹资活动现金流量
  cff_borrowing NUMERIC(18,2), -- 取得借款收到的现金
  cff_repayment_loan NUMERIC(18,2), -- 偿还债务支付的现金
  cff_dividend_payout NUMERIC(18,2), -- 分配股利、利润或偿付利息支付的现金
  cff_net_financing NUMERIC(18,2), -- 筹资活动产生的现金流量净额
  
  -- 现金及现金等价物净增加额
  net_increase_cash_equivalents NUMERIC(18,2), -- 现金及现金等价物净增加额
  beginning_cash_equivalents NUMERIC(18,2), -- 期初现金及现金等价物余额
  ending_cash_equivalents NUMERIC(18,2), -- 期末现金及现金等价物余额
  
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  remark TEXT
);

CREATE INDEX idx_fin_cashflow_company_period ON fin_cashflow_stmt(company_code, report_period);
```

### 4.2 添加注释
```sql
COMMENT ON TABLE fin_cashflow_stmt IS '现金流量表';
COMMENT ON COLUMN fin_cashflow_stmt.company_code IS '公司代码';
COMMENT ON COLUMN fin_cashflow_stmt.company_name IS '公司名称';
COMMENT ON COLUMN fin_cashflow_stmt.report_period IS '报告期间';
COMMENT ON COLUMN fin_cashflow_stmt.currency IS '货币单位';
COMMENT ON COLUMN fin_cashflow_stmt.cfo_sales_service IS '销售商品、提供劳务收到的现金';
COMMENT ON COLUMN fin_cashflow_stmt.cfo_receivables IS '收到的税费返还';
COMMENT ON COLUMN fin_cashflow_stmt.cfo_other_operating IS '收到其他与经营活动有关的现金';
COMMENT ON COLUMN fin_cashflow_stmt.cfo_subtotal_in IS '经营活动现金流入小计';
COMMENT ON COLUMN fin_cashflow_stmt.cfo_goods_services IS '购买商品、接受劳务支付的现金';
COMMENT ON COLUMN fin_cashflow_stmt.cfo_employee_payments IS '支付给职工以及为职工支付的现金';
COMMENT ON COLUMN fin_cashflow_stmt.cfo_payments_to_suppliers IS '支付的各项税费';
COMMENT ON COLUMN fin_cashflow_stmt.cfo_other_out IS '支付其他与经营活动有关的现金';
COMMENT ON COLUMN fin_cashflow_stmt.cfo_net_operating IS '经营活动产生的现金流量净额';
COMMENT ON COLUMN fin_cashflow_stmt.cfi_acquire_fixed IS '购建固定资产、无形资产和其他长期资产支付的现金';
COMMENT ON COLUMN fin_cashflow_stmt.cfi_dispose_fixed IS '处置固定资产、无形资产和其他长期资产收回的现金净额';
COMMENT ON COLUMN fin_cashflow_stmt.cfi_invest IS '投资支付的现金';
COMMENT ON COLUMN fin_cashflow_stmt.cfi_dividend_interest IS '取得投资收益收到的现金';
COMMENT ON COLUMN fin_cashflow_stmt.cfi_net_investing IS '投资活动产生的现金流量净额';
COMMENT ON COLUMN fin_cashflow_stmt.cff_borrowing IS '取得借款收到的现金';
COMMENT ON COLUMN fin_cashflow_stmt.cff_repayment_loan IS '偿还债务支付的现金';
COMMENT ON COLUMN fin_cashflow_stmt.cff_dividend_payout IS '分配股利、利润或偿付利息支付的现金';
COMMENT ON COLUMN fin_cashflow_stmt.cff_net_financing IS '筹资活动产生的现金流量净额';
COMMENT ON COLUMN fin_cashflow_stmt.net_increase_cash_equivalents IS '现金及现金等价物净增加额';
COMMENT ON COLUMN fin_cashflow_stmt.beginning_cash_equivalents IS '期初现金及现金等价物余额';
COMMENT ON COLUMN fin_cashflow_stmt.ending_cash_equivalents IS '期末现金及现金等价物余额';
```

## 五、数据类型推荐

### 5.1 金融数据类型选择
推荐使用 `NUMERIC(p,s)` 精确小数类型，避免浮点数精度问题：
- `NUMERIC(18,2)` - 通用金额字段，18位总数值，2位小数，适合各类财务数据的存储

### 5.2 其他常用数据类型
- 公司代码: `VARCHAR(20)` - 股票代码或其他识别码
- 公司名称: `VARCHAR(100)` - 公司全称
- 日期类型: `DATE` - 报告期等日期
- 时间戳: `TIMESTAMP` - 记录插入和更新时间
- 枚举类型: `VARCHAR(10)` - 期间类型(YEAR, QUARTER, MONTH)
- 货币代码: `CHAR(3)` - ISO 4217 三位字母码(CNY, USD)

## 六、约束与索引建议

### 6.1 主要约束
```sql
-- 为所有金额字段添加检查约束
ALTER TABLE fin_income_stmt ADD CONSTRAINT chk_positive_amount 
  CHECK (operating_revenue >= 0 OR operating_revenue IS NULL);

-- 公司代码约束
ALTER TABLE fin_income_stmt ADD CONSTRAINT chk_company_code 
  CHECK (length(trim(company_code)) > 0);

-- 完整的检查约束示例
ALTER TABLE fin_balance_stmt ADD CONSTRAINT chk_balance_equation
  CHECK (total_assets = liability_equity_total OR 
         abs(total_assets - liability_equity_total) < 0.01); -- 允许0.01以内的四舍五入误差
```

### 6.2 索引建议
- 按公司代码和报告期建立复合索引，支持多时间序列查询
- 为查询频繁的报表类型建立索引
- 定期分析查询计划，适当增加覆盖索引

## 七、扩展建议

### 7.1 财务分析计算字段
可以在数据库层面添加计算字段或视图，提供常用财务比率：
```sql
CREATE VIEW fin_analysis_ratios AS
SELECT 
  i.company_code,
  i.report_period,
  CASE 
    WHEN i.operating_revenue > 0 THEN i.net_profit / i.operating_revenue 
    ELSE NULL 
  END AS net_profit_margin, -- 净利润率
  CASE 
    WHEN b.total_assets > 0 THEN i.net_profit / b.total_assets 
    ELSE NULL 
  END AS roa, -- 资产回报率
  CASE 
    WHEN b.total_owners_equity > 0 THEN i.net_profit / b.total_owners_equity 
    ELSE NULL 
  END AS roe -- 净资产收益率
FROM fin_income_stmt i 
JOIN fin_balance_stmt b ON i.company_code = b.company_code 
  AND i.report_period = b.report_period;
```

## 八、数据管理建议

1. 严格控制数据录入权限，确保数据质量
2. 建立财务数据导入接口的校验规则
3. 定期备份财务数据，确保数据安全
4. 建立数据清理机制，保留必要的历史数据
5. 建立审计日志跟踪数据变更记录
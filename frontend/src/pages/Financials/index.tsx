import { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Tabs,
  Space,
  Tag,
  Button,
  Modal,
  Input,
  Select,
  Statistic,
  Row,
  Col,
  Typography,
  message,
  Progress,
  Popconfirm,
  Checkbox,
} from 'antd'
import {
  SearchOutlined,
  FileTextOutlined,
  DollarOutlined,
  BankOutlined,
  LineChartOutlined,
  EyeOutlined,
  ReloadOutlined,
  DownloadOutlined,
  StopOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import apiClient from '@/lib/api'
import type {
  EnterpriseFinancialSummary,
  EnterpriseFinancialDetail,
  BalanceSheet,
  IncomeStatement,
  CashFlowStatement,
  PaginatedResponse,
  GlobalFinancialStats,
  EnterpriseDataStatus,
} from '@/types'

const { TabPane } = Tabs
const { Text } = Typography
const { Option } = Select

// Format number to Chinese format (万/亿)
// Handles both number and string (from API Decimal serialization)
function formatAmount(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') return '-'
  
  // Convert string to number (API returns Decimal as string like "146695000000.00")
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  
  if (isNaN(numValue)) return '-'
  
  const absValue = Math.abs(numValue)
  if (absValue >= 1e8) {
    return (numValue / 1e8).toFixed(2) + '亿'
  } else if (absValue >= 1e4) {
    return (numValue / 1e4).toFixed(2) + '万'
  }
  return numValue.toFixed(2)
}

// Format date
function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function FinancialsPage() {
  // Enterprise list state
  const [loading, setLoading] = useState(false)
  const [enterprises, setEnterprises] = useState<EnterpriseFinancialSummary[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [search, setSearch] = useState('')
  const [hasDataFilter, setHasDataFilter] = useState<string>('')

  // Global statistics state
  const [globalStats, setGlobalStats] = useState<GlobalFinancialStats | null>(null)
  const [statsLoading, setStatsLoading] = useState(false)

  // Detail modal state
  const [detailVisible, setDetailVisible] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [selectedEnterprise, setSelectedEnterprise] = useState<EnterpriseFinancialDetail | null>(null)

  // Enterprise data status state
  const [enterpriseStatuses, setEnterpriseStatuses] = useState<Record<number, EnterpriseDataStatus>>({})
  const [updatingId, setUpdatingId] = useState<number | null>(null)

  // Batch refresh state
  const [batchRefreshRunning, setBatchRefreshRunning] = useState(false)
  const [batchRefreshProgress, setBatchRefreshProgress] = useState({ total: 0, completed: 0, failed: 0, currentEnterprise: '' })

  // Export state
  const [selectedRowKeys, setSelectedRowKeys] = useState<number[]>([])
  const [exporting, setExporting] = useState(false)
  const [yearModalVisible, setYearModalVisible] = useState(false)
  const [selectedYears, setSelectedYears] = useState<number[]>([2024, 2023, 2022, 2021])

  // Fetch global statistics
  const fetchGlobalStats = async () => {
    setStatsLoading(true)
    try {
      const response = await apiClient.get<GlobalFinancialStats>('/api/financials/stats')
      setGlobalStats(response.data)
    } catch (error) {
      console.error('Failed to fetch global stats:', error)
    } finally {
      setStatsLoading(false)
    }
  }

  // Fetch enterprise list with financial summary
  const fetchEnterprises = async () => {
    setLoading(true)
    try {
      const params: Record<string, unknown> = { page, page_size: pageSize }
      if (search) params.search = search
      if (hasDataFilter === 'yes') params.has_data = true
      else if (hasDataFilter === 'no') params.has_data = false

      const response = await apiClient.get<PaginatedResponse<EnterpriseFinancialSummary>>(
        '/api/financials/enterprises/summary',
        { params }
      )
      setEnterprises(response.data.items)
      setTotal(response.data.total)
    } catch (error) {
      message.error('获取企业列表失败')
    } finally {
      setLoading(false)
    }
  }

  // Fetch enterprise detail
  const fetchEnterpriseDetail = async (enterpriseId: number) => {
    setDetailLoading(true)
    try {
      const response = await apiClient.get<EnterpriseFinancialDetail>(
        `/api/financials/enterprises/${enterpriseId}`,
        { params: { years: 5 } }
      )
      setSelectedEnterprise(response.data)
      setDetailVisible(true)
    } catch (error) {
      message.error('获取财务数据失败')
    } finally {
      setDetailLoading(false)
    }
  }

  // Fetch enterprise data status
  const fetchEnterpriseStatus = async (enterpriseId: number) => {
    try {
      const response = await apiClient.get<EnterpriseDataStatus>(
        `/api/financials/enterprises/${enterpriseId}/status`
      )
      setEnterpriseStatuses(prev => ({
        ...prev,
        [enterpriseId]: response.data,
      }))
    } catch (error) {
      console.error('Failed to fetch enterprise status:', error)
    }
  }

  // Refresh enterprise data
  const refreshEnterpriseData = async (enterpriseId: number) => {
    setUpdatingId(enterpriseId)
    try {
      await apiClient.post(`/api/financials/enterprises/${enterpriseId}/refresh`)
      message.success('数据更新已触发')
      // Refresh status and list
      await fetchEnterpriseStatus(enterpriseId)
      await fetchEnterprises()
    } catch (error) {
      message.error('数据更新失败')
    } finally {
      setUpdatingId(null)
    }
  }

  // Batch refresh functions
  const startBatchRefresh = async () => {
    setBatchRefreshRunning(true)
    setBatchRefreshProgress({ total: 0, completed: 0, failed: 0, currentEnterprise: '' })
    try {
      const response = await apiClient.post('/api/financials/batch-refresh/start')
      message.success(response.data.message)
      pollBatchRefreshStatus()
    } catch (error: any) {
      message.error(error.response?.data?.message || '启动批量更新失败')
      setBatchRefreshRunning(false)
    }
  }

  const pollBatchRefreshStatus = async () => {
    try {
      const response = await apiClient.get('/api/financials/batch-refresh/status')
      const status = response.data
      setBatchRefreshProgress({
        total: status.total,
        completed: status.completed,
        failed: status.failed,
        currentEnterprise: status.current_enterprise || '',
      })

      if (status.is_running) {
        setTimeout(pollBatchRefreshStatus, 2000)
      } else {
        setBatchRefreshRunning(false)
        fetchGlobalStats()
        fetchEnterprises()
        if (status.completed > 0) {
          message.success(`批量更新完成！成功 ${status.completed} 家，失败 ${status.failed} 家`)
        }
      }
    } catch (error) {
      console.error('Failed to poll status:', error)
      setBatchRefreshRunning(false)
    }
  }

  const stopBatchRefresh = async () => {
    try {
      await apiClient.post('/api/financials/batch-refresh/stop')
      message.info('批量更新已停止')
    } catch (error) {
      message.error('停止失败')
    }
  }

  // Export functions
  const handleExport = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要导出的企业')
      return
    }
    if (selectedYears.length === 0) {
      message.warning('请选择要导出的年份')
      return
    }

    setExporting(true)
    try {
      const response = await apiClient.post(
        '/api/financials/export',
        {
          enterprise_ids: selectedRowKeys,
          years: selectedYears,
        },
        { responseType: 'blob' }
      )

      // Download file
      const blob = new Blob([response.data], {
        type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `financial_data_${new Date().toISOString().split('T')[0]}.xlsx`
      link.click()
      window.URL.revokeObjectURL(url)

      message.success(`成功导出 ${selectedRowKeys.length} 家企业的财务数据`)
      setYearModalVisible(false)
    } catch (error) {
      message.error('导出失败')
    } finally {
      setExporting(false)
    }
  }

  // Status tag renderer
  const getStatusTag = (status: string) => {
    const config: Record<string, { color: string; text: string }> = {
      complete: { color: 'success', text: '最新' },
      partial: { color: 'warning', text: '部分' },
      no_data: { color: 'default', text: '无数据' },
    }
    const { color, text } = config[status] || config.no_data
    return <Tag color={color}>{text}</Tag>
  }

  useEffect(() => {
    fetchEnterprises()
  }, [page, pageSize, search, hasDataFilter])

  // Fetch global stats on mount
  useEffect(() => {
    fetchGlobalStats()
  }, [])

  // Fetch statuses for all enterprises when list changes
  useEffect(() => {
    enterprises.forEach(enterprise => {
      if (!enterpriseStatuses[enterprise.enterprise_id]) {
        fetchEnterpriseStatus(enterprise.enterprise_id)
      }
    })
  }, [enterprises])

  // Enterprise list columns
  const columns: ColumnsType<EnterpriseFinancialSummary> = [
    {
      title: '代码',
      dataIndex: 'company_code',
      key: 'company_code',
      width: 80,
      render: (code) => <Tag color="blue">{code}</Tag>,
    },
    {
      title: '简称',
      dataIndex: 'company_name',
      key: 'company_name',
      width: 120,
      ellipsis: true,
    },
    {
      title: '资产负债表',
      dataIndex: 'balance_sheet_count',
      key: 'balance_sheet_count',
      width: 100,
      align: 'center',
      render: (count) => (
        <Tag color={count > 0 ? 'green' : 'default'}>{count} 条</Tag>
      ),
    },
    {
      title: '利润表',
      dataIndex: 'income_statement_count',
      key: 'income_statement_count',
      width: 100,
      align: 'center',
      render: (count) => (
        <Tag color={count > 0 ? 'green' : 'default'}>{count} 条</Tag>
      ),
    },
    {
      title: '现金流量表',
      dataIndex: 'cashflow_statement_count',
      key: 'cashflow_statement_count',
      width: 100,
      align: 'center',
      render: (count) => (
        <Tag color={count > 0 ? 'green' : 'default'}>{count} 条</Tag>
      ),
    },
    {
      title: '最新报告日期',
      dataIndex: 'latest_report_date',
      key: 'latest_report_date',
      width: 120,
      render: (date) => date ? formatDate(date) : '-',
    },
    {
      title: '数据状态',
      key: 'data_status',
      width: 100,
      align: 'center',
      render: (_, record) => {
        const status = enterpriseStatuses[record.enterprise_id]
        return status ? getStatusTag(status.status) : <Tag>-</Tag>
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 140,
      render: (_, record) => {
        const status = enterpriseStatuses[record.enterprise_id]
        const isUpdating = updatingId === record.enterprise_id
        return (
          <Space size="small">
            <Button
              type="link"
              size="small"
              icon={<EyeOutlined />}
              onClick={() => fetchEnterpriseDetail(record.enterprise_id)}
              disabled={record.balance_sheet_count === 0}
            >
              查看
            </Button>
            {status?.need_update && (
              <Button
                type="primary"
                size="small"
                icon={<ReloadOutlined spin={isUpdating} />}
                onClick={() => refreshEnterpriseData(record.enterprise_id)}
                disabled={isUpdating}
              >
                更新
              </Button>
            )}
          </Space>
        )
      },
    },
  ]

// Format EPS (handle string from API)
function formatEPS(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') return '-'
  const numValue = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(numValue)) return '-'
  return numValue.toFixed(4)
}

// Balance Sheet columns
const balanceSheetColumns: ColumnsType<BalanceSheet> = [
    { title: '报告日期', dataIndex: 'report_date', width: 100, render: formatDate },
    { title: '货币资金', dataIndex: 'cash', width: 100, align: 'right', render: formatAmount },
    { title: '应收账款', dataIndex: 'accounts_receivable', width: 100, align: 'right', render: formatAmount },
    { title: '存货', dataIndex: 'inventory', width: 100, align: 'right', render: formatAmount },
    { title: '流动资产', dataIndex: 'total_current_assets', width: 100, align: 'right', render: formatAmount },
    { title: '固定资产', dataIndex: 'fixed_assets', width: 100, align: 'right', render: formatAmount },
    { title: '资产总计', dataIndex: 'total_assets', width: 120, align: 'right', render: (v) => <Text strong>{formatAmount(v)}</Text> },
    { title: '流动负债', dataIndex: 'total_current_liabilities', width: 100, align: 'right', render: formatAmount },
    { title: '负债合计', dataIndex: 'total_liabilities', width: 100, align: 'right', render: formatAmount },
    { title: '所有者权益', dataIndex: 'total_equity', width: 100, align: 'right', render: formatAmount },
  ]

  // Income Statement columns
  const incomeStatementColumns: ColumnsType<IncomeStatement> = [
    { title: '报告日期', dataIndex: 'report_date', width: 100, render: formatDate },
    { title: '营业收入', dataIndex: 'operating_revenue', width: 120, align: 'right', render: (v) => <Text strong>{formatAmount(v)}</Text> },
    { title: '营业成本', dataIndex: 'operating_cost', width: 100, align: 'right', render: formatAmount },
    { title: '销售费用', dataIndex: 'selling_expenses', width: 100, align: 'right', render: formatAmount },
    { title: '管理费用', dataIndex: 'admin_expenses', width: 100, align: 'right', render: formatAmount },
    { title: '财务费用', dataIndex: 'financial_expenses', width: 100, align: 'right', render: formatAmount },
    { title: '营业利润', dataIndex: 'operating_profit', width: 100, align: 'right', render: formatAmount },
    { title: '净利润', dataIndex: 'net_profit', width: 120, align: 'right', render: (v) => {
      const numV = typeof v === 'string' ? parseFloat(v) : v
      return <Text strong type={numV !== null && numV < 0 ? 'danger' : undefined}>{formatAmount(v)}</Text>
    }},
    { title: '每股收益', dataIndex: 'basic_eps', width: 80, align: 'right', render: formatEPS },
  ]

  // Cash Flow Statement columns
  const cashFlowColumns: ColumnsType<CashFlowStatement> = [
    { title: '报告日期', dataIndex: 'report_date', width: 100, render: formatDate },
    { title: '经营现金流', dataIndex: 'net_cash_operating', width: 120, align: 'right', render: (v) => {
      const numV = typeof v === 'string' ? parseFloat(v) : v
      return <Text type={numV !== null && numV < 0 ? 'danger' : 'success'}>{formatAmount(v)}</Text>
    }},
    { title: '投资现金流', dataIndex: 'net_cash_investing', width: 100, align: 'right', render: formatAmount },
    { title: '筹资现金流', dataIndex: 'net_cash_financing', width: 100, align: 'right', render: formatAmount },
    { title: '现金净增加', dataIndex: 'net_cash_increase', width: 100, align: 'right', render: formatAmount },
    { title: '期末现金', dataIndex: 'cash_end_period', width: 100, align: 'right', render: formatAmount },
  ]

  // Calculate summary statistics (use global stats if available, otherwise local)
  const totalEnterprises = globalStats?.total_enterprises ?? total
  const withDataEnterprises = globalStats?.enterprises_with_data ?? enterprises.filter(e => e.balance_sheet_count > 0).length
  const dataRate = globalStats?.data_coverage_rate ?? (total > 0 ? ((enterprises.filter(e => e.balance_sheet_count > 0).length / Math.min(total, pageSize)) * 100).toFixed(1) : '0')
  const totalRecords = globalStats?.total_records ?? enterprises.reduce((sum, e) => sum + e.balance_sheet_count + e.income_statement_count + e.cashflow_statement_count, 0)

  // Row selection config for export
  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys: React.Key[]) => {
      setSelectedRowKeys(newSelectedRowKeys as number[])
    },
  }

  // Available years for export
  const availableYears = [2024, 2023, 2022, 2021, 2020]

  return (
    <div>
      {/* Summary Statistics */}
      <Card style={{ marginBottom: 16 }} loading={statsLoading && !globalStats}>
        <Row gutter={24}>
          <Col span={5}>
            <Statistic
              title="企业总数"
              value={totalEnterprises}
              prefix={<BankOutlined />}
            />
          </Col>
          <Col span={5}>
            <Statistic
              title="已导入财务数据"
              value={withDataEnterprises}
              suffix={globalStats ? `/ ${totalEnterprises}` : `/ ${pageSize}`}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Col>
          <Col span={5}>
            <Statistic
              title="数据覆盖率"
              value={dataRate}
              suffix="%"
              prefix={<LineChartOutlined />}
              valueStyle={{ color: parseFloat(String(dataRate)) > 90 ? '#3f8600' : '#cf1322' }}
            />
          </Col>
          <Col span={5}>
            <Statistic
              title="财务报表总记录"
              value={totalRecords}
              prefix={<DollarOutlined />}
            />
          </Col>
          <Col span={4}>
            {/* Batch Refresh Button */}
            {batchRefreshRunning ? (
              <div>
                <Button danger onClick={stopBatchRefresh} icon={<StopOutlined />}>
                  停止更新
                </Button>
                <Progress 
                  percent={Math.round((batchRefreshProgress.completed / batchRefreshProgress.total) * 100) || 0}
                  size="small"
                  style={{ marginTop: 8 }}
                />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  {batchRefreshProgress.completed}/{batchRefreshProgress.total}
                  {batchRefreshProgress.currentEnterprise && ` - ${batchRefreshProgress.currentEnterprise}`}
                </Text>
              </div>
            ) : (
              <Popconfirm
                title="批量更新所有企业财务数据"
                description="将更新所有4492家企业的财务数据，预计耗时约1小时，确定继续？"
                onConfirm={startBatchRefresh}
                okText="确定"
                cancelText="取消"
              >
                <Button type="primary" icon={<ReloadOutlined />}>
                  一键更新
                </Button>
              </Popconfirm>
            )}
          </Col>
        </Row>
      </Card>

      {/* Enterprise List */}
      <Card
        title={
          <Space>
            <span>企业财务数据</span>
            {selectedRowKeys.length > 0 && (
              <Tag color="blue">已选 {selectedRowKeys.length} 家</Tag>
            )}
          </Space>
        }
        extra={
          <Space>
            <Input
              placeholder="搜索代码/简称"
              prefix={<SearchOutlined />}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ width: 180 }}
              allowClear
            />
            <Select
              placeholder="数据状态"
              value={hasDataFilter || undefined}
              onChange={setHasDataFilter}
              style={{ width: 120 }}
              allowClear
            >
              <Option value="yes">有数据</Option>
              <Option value="no">无数据</Option>
            </Select>
            {selectedRowKeys.length > 0 && (
              <Button 
                type="primary" 
                icon={<DownloadOutlined />}
                onClick={() => setYearModalVisible(true)}
              >
                导出选中
              </Button>
            )}
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={enterprises}
          rowKey="enterprise_id"
          loading={loading}
          scroll={{ x: 800 }}
          size="small"
          rowSelection={rowSelection}
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 家企业`,
            onChange: (p, ps) => { setPage(p); setPageSize(ps) },
          }}
        />
      </Card>

      {/* Year Selection Modal for Export */}
      <Modal
        title="选择导出年份"
        open={yearModalVisible}
        onCancel={() => setYearModalVisible(false)}
        onOk={handleExport}
        confirmLoading={exporting}
        okText="导出"
        cancelText="取消"
      >
        <div style={{ marginBottom: 16 }}>
          <Text>将导出 <Text strong>{selectedRowKeys.length}</Text> 家企业的财务数据</Text>
        </div>
        <div>
          <Text>选择年份：</Text>
          <div style={{ marginTop: 8 }}>
            {availableYears.map(year => (
              <Checkbox
                key={year}
                checked={selectedYears.includes(year)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setSelectedYears([...selectedYears, year])
                  } else {
                    setSelectedYears(selectedYears.filter(y => y !== year))
                  }
                }}
                style={{ marginRight: 16 }}
              >
                {year}年
              </Checkbox>
            ))}
          </div>
        </div>
      </Modal>

      {/* Financial Detail Modal */}
      <Modal
        title={
          selectedEnterprise
            ? `${selectedEnterprise.company_code} - ${selectedEnterprise.company_name} 财务数据`
            : '财务数据详情'
        }
        open={detailVisible}
        onCancel={() => { setDetailVisible(false); setSelectedEnterprise(null) }}
        footer={null}
        width={1200}
        destroyOnClose
      >
        {detailLoading ? (
          <div style={{ textAlign: 'center', padding: 40 }}>加载中...</div>
        ) : selectedEnterprise ? (
          <Tabs defaultActiveKey="balance">
            <TabPane
              tab={<span><BankOutlined /> 资产负债表 ({selectedEnterprise.balance_sheets.length})</span>}
              key="balance"
            >
              <Table
                columns={balanceSheetColumns}
                dataSource={selectedEnterprise.balance_sheets}
                rowKey="id"
                size="small"
                scroll={{ x: 1100 }}
                pagination={false}
              />
            </TabPane>
            <TabPane
              tab={<span><LineChartOutlined /> 利润表 ({selectedEnterprise.income_statements.length})</span>}
              key="income"
            >
              <Table
                columns={incomeStatementColumns}
                dataSource={selectedEnterprise.income_statements}
                rowKey="id"
                size="small"
                scroll={{ x: 1000 }}
                pagination={false}
              />
            </TabPane>
            <TabPane
              tab={<span><DollarOutlined /> 现金流量表 ({selectedEnterprise.cash_flow_statements.length})</span>}
              key="cashflow"
            >
              <Table
                columns={cashFlowColumns}
                dataSource={selectedEnterprise.cash_flow_statements}
                rowKey="id"
                size="small"
                scroll={{ x: 700 }}
                pagination={false}
              />
            </TabPane>
          </Tabs>
        ) : null}
      </Modal>
    </div>
  )
}

export default FinancialsPage
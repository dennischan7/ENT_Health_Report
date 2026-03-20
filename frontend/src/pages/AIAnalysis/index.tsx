import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Select,
  Progress,
  Tag,
  message,
  Popconfirm,
  Typography,
  Row,
  Col,
  Statistic,
  Empty,
  Spin,
} from 'antd'
import {
  FileTextOutlined,
  DownloadOutlined,
  ThunderboltOutlined,
  ReloadOutlined,
  StopOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import apiClient from '@/lib/api'
import type { ReportTaskCreate } from '@/types'

const { Option } = Select
const { Text } = Typography

// Enterprise search result type
interface EnterpriseSearchResult {
  id: number
  company_code: string
  company_name: string
}

// Report task with enterprise name (from API)
interface ReportTaskWithEnterprise {
  task_id: string
  enterprise_id?: number
  enterprise_code?: string
  enterprise_name?: string
  report_type?: string
  status: string
  progress?: number
  message?: string
  error_message?: string
  result_url?: string
  created_at?: string
  updated_at?: string
  report_id?: number
}

// Task status configuration
const STATUS_CONFIG: Record<string, { color: string; text: string }> = {
  pending: { color: 'default', text: '等待中' },
  processing: { color: 'processing', text: '生成中' },
  completed: { color: 'success', text: '已完成' },
  failed: { color: 'error', text: '失败' },
}

function AIAnalysisPage() {
  // Enterprise selector state
  const [enterprises, setEnterprises] = useState<EnterpriseSearchResult[]>([])
  const [enterpriseLoading, setEnterpriseLoading] = useState(false)
  const [selectedEnterpriseId, setSelectedEnterpriseId] = useState<number | null>(null)
  const [searchValue, setSearchValue] = useState('')

  // Report generation state
  const [generating, setGenerating] = useState(false)
  const [currentTask, setCurrentTask] = useState<ReportTaskWithEnterprise | null>(null)
  const [pollingEnabled, setPollingEnabled] = useState(false)
  const pollingRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Report history state
  const [historyLoading, setHistoryLoading] = useState(false)
  const [reportHistory, setReportHistory] = useState<ReportTaskWithEnterprise[]>([])
  const [historyTotal, setHistoryTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)

  // Stats state
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    pending: 0,
    failed: 0,
  })

  // Search enterprises
  const searchEnterprises = async (query: string) => {
    if (!query || query.length < 1) {
      setEnterprises([])
      return
    }
    setEnterpriseLoading(true)
    try {
      const response = await apiClient.get<{ items: EnterpriseSearchResult[]; total: number }>(
        '/api/enterprises',
        { params: { search: query, page: 1, page_size: 20 } }
      )
      setEnterprises(response.data.items)
    } catch (error) {
      console.error('Failed to search enterprises:', error)
    } finally {
      setEnterpriseLoading(false)
    }
  }

  // Fetch report history
  const fetchReportHistory = async () => {
    setHistoryLoading(true)
    try {
      const response = await apiClient.get<{ items: ReportTaskWithEnterprise[]; total: number }>(
        '/api/reports',
        { params: { page, page_size: pageSize } }
      )
      setReportHistory(response.data.items)
      setHistoryTotal(response.data.total)

      // Calculate stats
      const allTasks = response.data.items
      setStats({
        total: response.data.total,
        completed: allTasks.filter(t => t.status === 'completed').length,
        pending: allTasks.filter(t => t.status === 'pending' || t.status === 'generating').length,
        failed: allTasks.filter(t => t.status === 'failed').length,
      })
    } catch (error) {
      message.error('获取报告历史失败')
    } finally {
      setHistoryLoading(false)
    }
  }

  // Fetch current task status (polling)
  const fetchTaskStatus = useCallback(async (taskId: string) => {
    try {
      const response = await apiClient.get<ReportTaskWithEnterprise>(`/api/reports/${taskId}/status`)
      const task = response.data
      setCurrentTask(task)

      // Stop polling if task is complete or failed
      if (task.status === 'completed' || task.status === 'failed') {
        setPollingEnabled(false)
        if (task.status === 'completed') {
          message.success('报告生成完成！')
        } else {
          message.error(`报告生成失败: ${task.error_message || '未知错误'}`)
        }
        fetchReportHistory()
      }
    } catch (error) {
      console.error('Failed to fetch task status:', error)
      setPollingEnabled(false)
    }
  }, [])

  // Start polling
  const startPolling = useCallback((taskId: string) => {
    setPollingEnabled(true)
    const poll = () => {
      fetchTaskStatus(taskId)
    }
    poll() // Initial fetch
    pollingRef.current = setInterval(poll, 5000) // Poll every 5 seconds
  }, [fetchTaskStatus])

  // Stop polling
  const stopPolling = useCallback(() => {
    setPollingEnabled(false)
    if (pollingRef.current) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
      }
    }
  }, [])

  // Polling effect
  useEffect(() => {
    if (pollingEnabled && currentTask) {
      // Polling is handled by startPolling
    } else {
      stopPolling()
    }
  }, [pollingEnabled, currentTask, stopPolling])

  // Fetch history on mount and page change
  useEffect(() => {
    fetchReportHistory()
  }, [page, pageSize])

  // Handle enterprise search
  const handleSearch = (value: string) => {
    setSearchValue(value)
    searchEnterprises(value)
  }

  // Handle enterprise selection
  const handleSelect = (enterpriseId: number) => {
    setSelectedEnterpriseId(enterpriseId)
  }

  // Generate report
  const handleGenerateReport = async () => {
    if (!selectedEnterpriseId) {
      message.warning('请选择企业')
      return
    }

    setGenerating(true)
    try {
      const createData: ReportTaskCreate = {
        enterprise_id: selectedEnterpriseId,
        report_type: 'health_diagnosis',
      }
      const response = await apiClient.post<{ task_id: string; status: string; message: string }>('/api/reports/generate', createData)
      const { task_id } = response.data
      message.success('报告生成任务已创建')
      startPolling(task_id)
      fetchReportHistory()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '创建报告任务失败')
    } finally {
      setGenerating(false)
    }
  }

  // Cancel current task
  const handleCancelTask = async () => {
    if (!currentTask) return
    try {
      await apiClient.delete(`/api/reports/${currentTask.task_id}`)
      message.info('任务已取消')
      stopPolling()
      setCurrentTask(null)
      fetchReportHistory()
    } catch (error) {
      message.error('取消任务失败')
    }
  }

  // Download report
  const handleDownload = async (task: ReportTaskWithEnterprise) => {
    if (!task.task_id) {
      message.error('任务ID不存在')
      return
    }
    try {
      const response = await apiClient.get(`/api/reports/${task.task_id}/download`, { responseType: 'blob' })
      const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `health_report_${task.enterprise_code || 'enterprise'}_${task.task_id}.docx`
      link.click()
      window.URL.revokeObjectURL(url)
    } catch (error) {
      message.error('下载报告失败')
    }
  }

  // Get status tag
  const getStatusTag = (status: string) => {
    const config = STATUS_CONFIG[status] || STATUS_CONFIG.pending
    return <Tag color={config.color}>{config.text}</Tag>
  }

  // Format date
  const formatDate = (dateStr: string | undefined) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleString('zh-CN')
  }

  // History table columns
  const columns: ColumnsType<ReportTaskWithEnterprise> = [
    {
      title: '企业代码',
      dataIndex: 'enterprise_code',
      key: 'enterprise_code',
      width: 100,
      render: (code) => <Tag color="blue">{code}</Tag>,
    },
    {
      title: '企业名称',
      dataIndex: 'enterprise_name',
      key: 'enterprise_name',
      width: 150,
      ellipsis: true,
    },
    {
      title: '报告类型',
      dataIndex: 'report_type',
      key: 'report_type',
      width: 120,
      render: (type) => {
        const typeMap: Record<string, string> = {
          health_diagnosis: '健康诊断报告',
        }
        return typeMap[type] || type
      },
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => getStatusTag(status),
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress, record) => {
        if (record.status === 'completed') {
          return <Progress percent={100} size="small" status="success" />
        }
        if (record.status === 'failed') {
          return <Progress percent={progress || 0} size="small" status="exception" />
        }
        return <Progress percent={progress || 0} size="small" />
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: formatDate,
    },
    {
      title: '完成时间',
      dataIndex: 'completed_at',
      key: 'completed_at',
      width: 160,
      render: formatDate,
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Space>
          {record.status === 'completed' && (
            <Button
              type="link"
              size="small"
              icon={<DownloadOutlined />}
              onClick={() => handleDownload(record)}
            >
              下载
            </Button>
          )}
          {record.status === 'failed' && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              {record.error_message || '生成失败'}
            </Text>
          )}
        </Space>
      ),
    },
  ]

  return (
    <div>
      {/* Stats Card */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={24}>
          <Col span={6}>
            <Statistic
              title="报告总数"
              value={stats.total}
              prefix={<FileTextOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="已完成"
              value={stats.completed}
              valueStyle={{ color: '#3f8600' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="处理中"
              value={stats.pending}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="失败"
              value={stats.failed}
              valueStyle={{ color: '#cf1322' }}
            />
          </Col>
        </Row>
      </Card>

      {/* Generate Report Card */}
      <Card title="生成诊断报告" style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {/* Enterprise Selector */}
          <div>
            <Text strong style={{ display: 'block', marginBottom: 8 }}>
              选择企业
            </Text>
            <Select
              showSearch
              placeholder="搜索企业代码或名称..."
              style={{ width: '100%', maxWidth: 400 }}
              defaultActiveFirstOption={false}
              showArrow={false}
              filterOption={false}
              onSearch={handleSearch}
              onSelect={handleSelect}
              loading={enterpriseLoading}
              notFoundContent={
                enterpriseLoading ? (
                  <Spin size="small" />
                ) : searchValue ? (
                  <Empty description="未找到企业" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                ) : (
                  <Empty description="输入关键词搜索" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                )
              }
            >
              {enterprises.map((e) => (
                <Option key={e.id} value={e.id}>
                  <Space>
                    <Tag color="blue">{e.company_code}</Tag>
                    <span>{e.company_name}</span>
                  </Space>
                </Option>
              ))}
            </Select>
          </div>

          {/* Current Task Progress */}
          {currentTask && (
            <Card size="small" style={{ background: '#fafafa' }}>
              <Space direction="vertical" style={{ width: '100%' }}>
                <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                  <Text>
                    当前任务: <Tag color="blue">{currentTask.enterprise_code}</Tag>
                    {currentTask.enterprise_name}
                  </Text>
                  {getStatusTag(currentTask.status)}
                </Space>
                {currentTask.status === 'generating' && (
                  <Progress
                    percent={currentTask.progress || 0}
                    status="active"
                    strokeColor={{ from: '#108ee9', to: '#87d068' }}
                  />
                )}
                {currentTask.status === 'completed' && (
                  <Button
                    type="primary"
                    icon={<DownloadOutlined />}
                    onClick={() => handleDownload(currentTask)}
                  >
                    下载报告
                  </Button>
                )}
              </Space>
            </Card>
          )}

          {/* Generate Button */}
          <Space>
            <Popconfirm
              title="确认生成报告"
              description="将使用 AI 分析企业财务数据并生成健康诊断报告，确定继续？"
              onConfirm={handleGenerateReport}
              disabled={!selectedEnterpriseId || generating || pollingEnabled}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                loading={generating}
                disabled={!selectedEnterpriseId || pollingEnabled}
              >
                生成报告
              </Button>
            </Popconfirm>
            {pollingEnabled && (
              <Button
                danger
                icon={<StopOutlined />}
                onClick={handleCancelTask}
              >
                取消任务
              </Button>
            )}
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchReportHistory}
            >
              刷新
            </Button>
          </Space>
        </Space>
      </Card>

      {/* Report History Card */}
      <Card title="报告历史">
        <Table
          columns={columns}
          dataSource={reportHistory}
          rowKey="id"
          loading={historyLoading}
          size="small"
          pagination={{
            current: page,
            pageSize,
            total: historyTotal,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条`,
            onChange: (p, ps) => { setPage(p); setPageSize(ps) },
          }}
        />
      </Card>
    </div>
  )
}

export default AIAnalysisPage
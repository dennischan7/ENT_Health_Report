import { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  message,
  Popconfirm,
  Tag,
} from 'antd'
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import apiClient from '@/lib/api'
import type { AIConfig, AIConfigCreate, AIConfigUpdate } from '@/types'

const { Option } = Select
const { Password } = Input

// Provider options
const PROVIDERS = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'azure', label: 'Azure OpenAI' },
  { value: 'custom', label: 'Custom' },
]

// Common models per provider
const PROVIDER_MODELS: Record<string, string[]> = {
  openai: ['gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
  deepseek: ['deepseek-chat', 'deepseek-coder'],
  anthropic: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku'],
  azure: ['gpt-4o', 'gpt-4-turbo', 'gpt-35-turbo'],
  custom: [],
}

interface AIConfigFormData {
  name: string
  provider: string
  api_base_url: string
  api_key: string
  model: string
  temperature: number
  max_tokens: number
  is_default?: boolean
  is_active?: boolean
}

function AIConfigPage() {
  const [loading, setLoading] = useState(false)
  const [configs, setConfigs] = useState<AIConfig[]>([])
  const [total, setTotal] = useState(0)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingConfig, setEditingConfig] = useState<AIConfig | null>(null)
  const [form] = Form.useForm<AIConfigFormData>()
  const [submitting, setSubmitting] = useState(false)
  const [activatingId, setActivatingId] = useState<number | null>(null)

  // Fetch configs
  const fetchConfigs = async () => {
    setLoading(true)
    try {
      const response = await apiClient.get<{ items: AIConfig[]; total: number }>('/api/ai-configs')
      setConfigs(response.data.items)
      setTotal(response.data.total)
    } catch (error) {
      message.error('获取配置列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchConfigs()
  }, [])

  // Create new config
  const handleCreate = () => {
    setEditingConfig(null)
    form.resetFields()
    // Set default values
    form.setFieldsValue({
      temperature: 0.7,
      max_tokens: 4096,
      is_active: true,
    })
    setModalVisible(true)
  }

  // Edit existing config
  const handleEdit = (record: AIConfig) => {
    setEditingConfig(record)
    form.setFieldsValue({
      name: record.name,
      provider: record.provider,
      api_base_url: record.api_base_url,
      api_key: '', // Don't show existing key
      model: record.model,
      temperature: record.temperature,
      max_tokens: record.max_tokens,
      is_default: record.is_default,
      is_active: record.is_active,
    })
    setModalVisible(true)
  }

  // Delete config
  const handleDelete = async (id: number) => {
    try {
      await apiClient.delete(`/api/ai-configs/${id}`)
      message.success('删除成功')
      fetchConfigs()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

  // Activate config
  const handleActivate = async (id: number) => {
    setActivatingId(id)
    try {
      await apiClient.put(`/api/ai-configs/${id}/activate`)
      message.success('激活成功')
      fetchConfigs()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '激活失败')
    } finally {
      setActivatingId(null)
    }
  }

  // Submit form
  const handleSubmit = async (values: AIConfigFormData) => {
    setSubmitting(true)
    try {
      if (editingConfig) {
        // Update existing config
        const updateData: AIConfigUpdate = { ...values }
        if (!updateData.api_key) {
          delete updateData.api_key // Don't update if empty
        }
        await apiClient.put(`/api/ai-configs/${editingConfig.id}`, updateData)
        message.success('更新成功')
      } else {
        // Create new config
        if (!values.api_key) {
          message.error('API Key 不能为空')
          return
        }
        const createData: AIConfigCreate = {
          name: values.name,
          provider: values.provider,
          model: values.model,
          api_base_url: values.api_base_url,
          api_key: values.api_key,
          temperature: values.temperature,
          max_tokens: values.max_tokens,
          is_default: values.is_default,
          is_active: values.is_active,
        }
        await apiClient.post('/api/ai-configs', createData)
        message.success('创建成功')
      }
      setModalVisible(false)
      fetchConfigs()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    } finally {
      setSubmitting(false)
    }
  }

  // Mask API key
  const maskApiKey = (key: string): string => {
    if (!key) return '-'
    if (key.length <= 8) return '***'
    return `${key.slice(0, 4)}${'*'.repeat(Math.min(key.length - 8, 20))}${key.slice(-4)}`
  }

  // Get provider display name
  const getProviderLabel = (provider: string): string => {
    const found = PROVIDERS.find(p => p.value === provider)
    return found?.label || provider
  }

  // Table columns
  const columns: ColumnsType<AIConfig> = [
    {
      title: '配置名称',
      dataIndex: 'name',
      key: 'name',
      width: 150,
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      width: 120,
      render: (provider) => (
        <Tag color="blue">{getProviderLabel(provider)}</Tag>
      ),
    },
    {
      title: '模型',
      dataIndex: 'model',
      key: 'model',
      width: 150,
    },
    {
      title: 'API Key',
      dataIndex: 'api_key',
      key: 'api_key',
      width: 200,
      render: (key) => (
        <span style={{ fontFamily: 'monospace', color: '#666' }}>
          {maskApiKey(key)}
        </span>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (active) => (
        <Tag color={active ? 'green' : 'default'}>
          {active ? '已激活' : '未激活'}
        </Tag>
      ),
    },
    {
      title: '温度',
      dataIndex: 'temperature',
      key: 'temperature',
      width: 80,
      render: (temp) => temp?.toFixed(2) || '-',
    },
    {
      title: '最大Token',
      dataIndex: 'max_tokens',
      key: 'max_tokens',
      width: 100,
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
          >
            编辑
          </Button>
          {!record.is_active && (
            <Button
              type="link"
              icon={<CheckCircleOutlined />}
              loading={activatingId === record.id}
              onClick={() => handleActivate(record.id)}
            >
              激活
            </Button>
          )}
          <Popconfirm
            title="确定要删除这个配置吗？"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  // Watch provider change to update model options
  const selectedProvider = Form.useWatch('provider', form)

  return (
    <div>
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
          <div>
            <Tag color="blue">共 {total} 个配置</Tag>
          </div>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>
            新建配置
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={configs}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 条`,
          }}
        />
      </Card>

      <Modal
        title={editingConfig ? '编辑配置' : '新建配置'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={submitting}
        destroyOnClose
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="name"
            label="配置名称"
            rules={[{ required: true, message: '请输入配置名称' }]}
          >
            <Input placeholder="例如：生产环境 GPT-4" maxLength={100} />
          </Form.Item>

          <Form.Item
            name="provider"
            label="提供商"
            rules={[{ required: true, message: '请选择提供商' }]}
          >
            <Select placeholder="选择提供商" showSearch>
              {PROVIDERS.map(p => (
                <Option key={p.value} value={p.value}>{p.label}</Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="api_base_url"
            label="API Base URL"
            rules={[{ required: true, message: '请输入 API Base URL' }]}
          >
            <Input placeholder="例如：https://api.openai.com/v1" />
          </Form.Item>

          <Form.Item
            name="api_key"
            label="API Key"
            rules={editingConfig ? [] : [{ required: true, message: '请输入 API Key' }]}
          >
            <Password 
              placeholder={editingConfig ? '留空则不修改' : '请输入 API Key'} 
              autoComplete="new-password"
            />
          </Form.Item>

          <Form.Item
            name="model"
            label="模型名称"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            {selectedProvider && PROVIDER_MODELS[selectedProvider]?.length > 0 ? (
              <Select placeholder="选择模型" showSearch allowClear>
                {PROVIDER_MODELS[selectedProvider].map(m => (
                  <Option key={m} value={m}>{m}</Option>
                ))}
              </Select>
            ) : (
              <Input placeholder="例如：gpt-4o" />
            )}
          </Form.Item>

          <Form.Item
            name="temperature"
            label="Temperature"
            tooltip="控制输出的随机性，0-2之间，值越低输出越确定"
          >
            <InputNumber
              min={0}
              max={2}
              step={0.1}
              precision={2}
              style={{ width: '100%' }}
              placeholder="0.7"
            />
          </Form.Item>

          <Form.Item
            name="max_tokens"
            label="Max Tokens"
            tooltip="最大输出 Token 数量"
          >
            <InputNumber
              min={1}
              max={128000}
              step={256}
              style={{ width: '100%' }}
              placeholder="4096"
            />
          </Form.Item>

          {editingConfig && (
            <Form.Item label="状态">
              <Tag color={editingConfig.is_active ? 'green' : 'default'}>
                {editingConfig.is_active ? '已激活' : '未激活'}
              </Tag>
              <span style={{ marginLeft: 8, color: '#999', fontSize: 12 }}>
                (使用列表中的"激活"按钮切换状态)
              </span>
            </Form.Item>
          )}
        </Form>
      </Modal>
    </div>
  )
}

export default AIConfigPage
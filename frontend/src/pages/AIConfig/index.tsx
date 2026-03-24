import { useState, useEffect } from 'react'
import {
  Card,
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  message,
  Popconfirm,
  Tag,
  AutoComplete,
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

// Provider options - match backend AIProvider enum
const PROVIDERS = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'deepseek', label: 'DeepSeek' },
  { value: 'anthropic', label: 'Anthropic' },
  { value: 'qwen', label: '阿里 (通义千问)' },
  { value: 'kimi', label: 'Moonshot (Kimi)' },
  { value: 'glm', label: '智谱 (GLM)' },
  { value: 'baidu', label: '百度' },
  { value: 'tencent', label: '腾讯' },
  { value: 'minimax', label: 'MiniMax' },
  { value: 'gemini', label: 'Google Gemini' },
  { value: 'openai-compatible', label: 'OpenAI兼容' },
]

// Common models per provider
const PROVIDER_MODELS: Record<string, string[]> = {
  openai: ['gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
  deepseek: ['deepseek-chat', 'deepseek-coder'],
  anthropic: ['claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku', 'claude-3-5-sonnet'],
  qwen: ['qwen-turbo', 'qwen-plus', 'qwen-max', 'qwen-max-longcontext', 'qwen2.5-72b-instruct', 'qwen2.5-32b-instruct', 'qwen3-235b-a22b', 'qwen3-32b'],
  kimi: ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k'],
  glm: ['glm-4', 'glm-4-plus', 'glm-4-air', 'glm-3-turbo'],
  baidu: ['ERNIE-Bot-4', 'ERNIE-Bot', 'ERNIE-Bot-turbo'],
  tencent: ['hunyuan-lite', 'hunyuan-standard', 'hunyuan-pro'],
  minimax: ['abab5.5-chat', 'abab5.5s-chat'],
  gemini: ['gemini-pro', 'gemini-1.5-pro', 'gemini-1.5-flash'],
  'openai-compatible': [],
}

interface AIConfigFormData {
  config_name: string
  provider: string
  model_name: string
  api_key: string
  description?: string
  is_default?: boolean
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
      is_default: false,
    })
    setModalVisible(true)
  }

  // Edit existing config
  const handleEdit = (record: AIConfig) => {
    setEditingConfig(record)
    form.setFieldsValue({
      config_name: record.config_name,
      provider: record.provider,
      model_name: record.model_name,
      api_key: '', // Don't show existing key
      description: record.description,
      is_default: record.is_default,
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
      await apiClient.post(`/api/ai-configs/${id}/activate`)
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
          config_name: values.config_name,
          provider: values.provider,
          model_name: values.model_name,
          api_key: values.api_key,
          description: values.description,
          is_default: values.is_default,
        }
        await apiClient.post('/api/ai-configs', createData)
        message.success('创建成功')
      }
      setModalVisible(false)
      fetchConfigs()
    } catch (error: any) {
      // 详细错误提示
      let errorMessage = '操作失败'

      if (error.response) {
        // 服务器返回的错误
        const detail = error.response.data?.detail
        if (typeof detail === 'string') {
          errorMessage = detail
        } else if (detail?.message) {
          errorMessage = detail.message
        } else if (error.response.status === 422) {
          // 验证错误
          const errors = error.response.data?.detail
          if (Array.isArray(errors)) {
            errorMessage = errors.map((e: any) => e.msg).join(', ')
          } else {
            errorMessage = '数据验证失败，请检查输入'
          }
        } else if (error.response.status === 401) {
          errorMessage = '未登录或登录已过期'
        } else if (error.response.status === 403) {
          errorMessage = '没有权限执行此操作'
        }
      } else if (error.request) {
        // 请求发送但没有响应
        errorMessage = '网络错误，请检查网络连接'
      } else {
        // 请求配置错误
        errorMessage = error.message || '操作失败'
      }

      message.error(errorMessage)
      console.error('AI配置保存失败:', error)
    } finally {
      setSubmitting(false)
    }
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
      dataIndex: 'config_name',
      key: 'config_name',
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
      dataIndex: 'model_name',
      key: 'model_name',
      width: 150,
    },
    {
      title: 'API Key',
      dataIndex: 'api_key_set',
      key: 'api_key_set',
      width: 120,
      render: (set) => (
        <Tag color={set ? 'green' : 'default'}>
          {set ? '已配置' : '未配置'}
        </Tag>
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
            name="config_name"
            label="配置名称"
            rules={[{ required: true, message: '请输入配置名称' }]}
          >
            <Input placeholder="例如：生产环境 DeepSeek" maxLength={100} />
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
            name="model_name"
            label="模型名称"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            <AutoComplete
              placeholder="选择或输入模型名称"
              options={
                selectedProvider && PROVIDER_MODELS[selectedProvider]
                  ? PROVIDER_MODELS[selectedProvider].map(m => ({ value: m }))
                  : []
              }
              filterOption={(inputValue, option) =>
                option!.value.toLowerCase().indexOf(inputValue.toLowerCase()) !== -1
              }
            />
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea placeholder="可选的配置描述" rows={2} maxLength={500} />
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
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
  Descriptions,
  Spin,
  Divider,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  EyeOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import apiClient from '@/lib/api'
import type { EnterpriseDetail } from '@/types'

const { Option } = Select

interface Enterprise {
  id: number
  category_name: string
  industry_code: string
  industry_name: string
  company_code: string
  company_name: string
  created_at: string
  updated_at: string
}

interface EnterpriseForm {
  category_name: string
  industry_code: string
  industry_name: string
  company_code: string
  company_name: string
}

function EnterprisesPage() {
  const [loading, setLoading] = useState(false)
  const [enterprises, setEnterprises] = useState<Enterprise[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('')
  const [industryFilter, setIndustryFilter] = useState<string>('')
  const [categories, setCategories] = useState<string[]>([])
  const [industries, setIndustries] = useState<string[]>([])
  const [modalVisible, setModalVisible] = useState(false)
  const [editingEnterprise, setEditingEnterprise] = useState<Enterprise | null>(null)
  const [form] = Form.useForm<EnterpriseForm>()
  const [detailVisible, setDetailVisible] = useState(false)
  const [detailLoading, setDetailLoading] = useState(false)
  const [detailData, setDetailData] = useState<EnterpriseDetail | null>(null)

  const fetchCategories = async () => {
    try {
      const response = await apiClient.get('/api/enterprises/categories/list')
      setCategories(response.data)
    } catch (error) {
      console.error('Failed to fetch categories')
    }
  }

  const fetchIndustries = async () => {
    try {
      const response = await apiClient.get('/api/enterprises/industries/list')
      setIndustries(response.data)
    } catch (error) {
      console.error('Failed to fetch industries')
    }
  }

  const fetchEnterprises = async () => {
    setLoading(true)
    try {
      const params: any = { page, page_size: pageSize }
      if (search) params.search = search
      if (categoryFilter) params.category_name = categoryFilter
      if (industryFilter) params.industry_name = industryFilter
      const response = await apiClient.get('/api/enterprises', { params })
      setEnterprises(response.data.items)
      setTotal(response.data.total)
    } catch (error) {
      message.error('获取企业列表失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchCategories(); fetchIndustries() }, [])
  useEffect(() => { fetchEnterprises() }, [page, pageSize, search, categoryFilter, industryFilter])

  const handleCreate = () => {
    setEditingEnterprise(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: Enterprise) => {
    setEditingEnterprise(record)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await apiClient.delete(`/api/enterprises/${id}`)
      message.success('删除成功')
      fetchEnterprises()
    } catch (error) {
      message.error('删除失败')
    }
  }

  const handleViewDetail = async (id: number) => {
    setDetailVisible(true)
    setDetailLoading(true)
    setDetailData(null)
    try {
      const response = await apiClient.get(`/api/enterprises/${id}/detail`)
      setDetailData(response.data)
    } catch (error) {
      message.error('获取企业详情失败')
      setDetailVisible(false)
    } finally {
      setDetailLoading(false)
    }
  }

  const handleSubmit = async (values: EnterpriseForm) => {
    try {
      if (editingEnterprise) {
        await apiClient.put(`/api/enterprises/${editingEnterprise.id}`, values)
        message.success('更新成功')
      } else {
        await apiClient.post('/api/enterprises', values)
        message.success('创建成功')
      }
      setModalVisible(false)
      fetchEnterprises()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    }
  }

  const columns: ColumnsType<Enterprise> = [
    {
      title: '代码',
      dataIndex: 'company_code',
      key: 'company_code',
      width: 80,
      render: (t) => <Tag color="blue">{t}</Tag>
    },
    {
      title: '简称',
      dataIndex: 'company_name',
      key: 'company_name',
      width: 100
    },
    {
      title: '门类',
      dataIndex: 'category_name',
      key: 'category_name',
      width: 120,
      ellipsis: true
    },
    {
      title: '行业代码',
      dataIndex: 'industry_code',
      key: 'industry_code',
      width: 70
    },
    {
      title: '行业名称',
      dataIndex: 'industry_name',
      key: 'industry_name',
      width: 150,
      ellipsis: true
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      render: (_, r) => (
        <Space>
          <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => handleViewDetail(r.id)}>详情</Button>
          <Button type="link" size="small" onClick={() => handleEdit(r)}>编辑</Button>
          <Popconfirm title="确定?" onConfirm={() => handleDelete(r.id)}>
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      )
    },
  ]

  return (
    <div>
      <Card>
        <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', gap: 8 }}>
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
              placeholder="门类"
              value={categoryFilter || undefined}
              onChange={setCategoryFilter}
              style={{ width: 130 }}
              allowClear
              showSearch
            >
              {categories.map(c => <Option key={c} value={c}>{c}</Option>)}
            </Select>
            <Select
              placeholder="行业"
              value={industryFilter || undefined}
              onChange={setIndustryFilter}
              style={{ width: 150 }}
              allowClear
              showSearch
            >
              {industries.map(i => <Option key={i} value={i}>{i}</Option>)}
            </Select>
          </Space>
          <Button type="primary" icon={<PlusOutlined />} onClick={handleCreate}>新建</Button>
        </div>
        <Tag color="blue">共 {total} 家</Tag>
        <Table
          columns={columns}
          dataSource={enterprises}
          rowKey="id"
          loading={loading}
          scroll={{ x: 700 }}
          size="small"
          pagination={{
            current: page,
            pageSize,
            total,
            showSizeChanger: true,
            showTotal: (t) => `共 ${t} 条`,
            onChange: (p, ps) => { setPage(p); setPageSize(ps) }
          }}
        />
      </Card>
      <Modal
        title={editingEnterprise ? '编辑' : '新建'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          <Form.Item name="company_code" label="代码" rules={[{ required: true }]}>
            <Input maxLength={10} />
          </Form.Item>
          <Form.Item name="company_name" label="简称" rules={[{ required: true }]}>
            <Input maxLength={100} />
          </Form.Item>
          <Form.Item name="category_name" label="门类" rules={[{ required: true }]}>
            <Select showSearch allowClear>
              {categories.map(c => <Option key={c} value={c}>{c}</Option>)}
            </Select>
          </Form.Item>
          <Form.Item name="industry_code" label="行业代码" rules={[{ required: true }]}>
            <Input maxLength={10} />
          </Form.Item>
          <Form.Item name="industry_name" label="行业名称" rules={[{ required: true }]}>
            <Select showSearch allowClear>
              {industries.map(i => <Option key={i} value={i}>{i}</Option>)}
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 企业详情弹窗 */}
      <Modal
        title={detailData ? `${detailData.company_code} - ${detailData.company_name}` : '企业详情'}
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={800}
        destroyOnClose
      >
        <Spin spinning={detailLoading}>
          {detailData && (
            <>
              <Descriptions title="基本信息" bordered column={2} size="small">
                <Descriptions.Item label="公司名称">{detailData.company_name || '-'}</Descriptions.Item>
                <Descriptions.Item label="英文名称">{detailData.english_name || '-'}</Descriptions.Item>
                <Descriptions.Item label="股票代码">
                  <Tag color="blue">{detailData.company_code}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="行业">{detailData.industry_name || '-'}</Descriptions.Item>
                <Descriptions.Item label="法人代表" span={2}>{detailData.legal_representative || '-'}</Descriptions.Item>
              </Descriptions>

              <Divider style={{ margin: '16px 0' }} />

              <Descriptions title="注册信息" bordered column={2} size="small">
                <Descriptions.Item label="注册资金">
                  {detailData.registered_capital ? `${detailData.registered_capital.toLocaleString()} 万元` : '-'}
                </Descriptions.Item>
                <Descriptions.Item label="成立日期">{detailData.establish_date || '-'}</Descriptions.Item>
                <Descriptions.Item label="上市日期">{detailData.listing_date || '-'}</Descriptions.Item>
                <Descriptions.Item label="门类">{detailData.category_name || '-'}</Descriptions.Item>
                <Descriptions.Item label="注册地址" span={2}>{detailData.registered_address || '-'}</Descriptions.Item>
                <Descriptions.Item label="办公地址" span={2}>{detailData.office_address || '-'}</Descriptions.Item>
              </Descriptions>

              <Divider style={{ margin: '16px 0' }} />

              <Descriptions title="联系方式" bordered column={2} size="small">
                <Descriptions.Item label="联系电话">{detailData.phone || '-'}</Descriptions.Item>
                <Descriptions.Item label="电子邮箱">{detailData.email || '-'}</Descriptions.Item>
                <Descriptions.Item label="传真">{detailData.fax || '-'}</Descriptions.Item>
                <Descriptions.Item label="官方网站">
                  {detailData.website ? (
                    <a href={detailData.website} target="_blank" rel="noopener noreferrer">{detailData.website}</a>
                  ) : '-'}
                </Descriptions.Item>
              </Descriptions>

              <Divider style={{ margin: '16px 0' }} />

              <Descriptions title="经营信息" bordered column={1} size="small">
                <Descriptions.Item label="主营业务">
                  <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {detailData.main_business || '-'}
                  </div>
                </Descriptions.Item>
                <Descriptions.Item label="经营范围">
                  <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {detailData.business_scope || '-'}
                  </div>
                </Descriptions.Item>
                <Descriptions.Item label="机构简介">
                  <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {detailData.company_profile || '-'}
                  </div>
                </Descriptions.Item>
              </Descriptions>
            </>
          )}
        </Spin>
      </Modal>
    </div>
  )
}

export default EnterprisesPage
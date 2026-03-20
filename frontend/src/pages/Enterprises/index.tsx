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
  DatePicker,
  message,
  Popconfirm,
  Tag,
  Descriptions,
  Spin,
  Divider,
  Typography,
  Row,
  Col,
} from 'antd'
import {
  PlusOutlined,
  SearchOutlined,
  EyeOutlined,
  SaveOutlined,
} from '@ant-design/icons'
import type { ColumnsType } from 'antd/es/table'
import dayjs from 'dayjs'
import apiClient from '@/lib/api'
import type { EnterpriseDetail, User } from '@/types'

const { Option } = Select
const { Title } = Typography
const { TextArea } = Input

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
  // 基本信息
  category_name: string
  industry_code: string
  industry_name: string
  company_code: string
  company_name: string
  // 扩展字段
  english_name?: string
  legal_representative?: string
  registered_capital?: number
  establish_date?: dayjs.Dayjs | null
  listing_date?: dayjs.Dayjs | null
  website?: string
  email?: string
  phone?: string
  fax?: string
  registered_address?: string
  office_address?: string
  main_business?: string
  business_scope?: string
  company_profile?: string
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
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [editLoading, setEditLoading] = useState(false)

  // 获取当前用户信息
  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      setCurrentUser(JSON.parse(userStr))
    }
  }, [])

  const isAdmin = currentUser?.role === 'admin'

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

  const handleEdit = async (record: Enterprise) => {
    setEditingEnterprise(record)
    setEditLoading(true)
    try {
      const response = await apiClient.get(`/api/enterprises/${record.id}/detail`)
      const detail = response.data
      form.setFieldsValue({
        ...detail,
        establish_date: detail.establish_date ? dayjs(detail.establish_date) : null,
        listing_date: detail.listing_date ? dayjs(detail.listing_date) : null,
      })
      setModalVisible(true)
    } catch (error) {
      message.error('获取企业详情失败')
    } finally {
      setEditLoading(false)
    }
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

  const handleSave = async (values: EnterpriseForm, closeAfterSave: boolean = true) => {
    try {
      // 格式化日期字段
      const submitData = {
        ...values,
        establish_date: values.establish_date ? values.establish_date.format('YYYY-MM-DD') : null,
        listing_date: values.listing_date ? values.listing_date.format('YYYY-MM-DD') : null,
      }
      
      if (editingEnterprise) {
        await apiClient.put(`/api/enterprises/${editingEnterprise.id}`, submitData)
        message.success(closeAfterSave ? '保存成功' : '已暂存')
      } else {
        await apiClient.post('/api/enterprises', submitData)
        message.success(closeAfterSave ? '创建成功' : '已暂存')
      }
      
      if (closeAfterSave) {
        setModalVisible(false)
      }
      fetchEnterprises()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '操作失败')
    }
  }

  const handleSubmit = async (values: EnterpriseForm) => {
    await handleSave(values, true)
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
          <Button type="link" size="small" loading={editLoading && editingEnterprise?.id === r.id} onClick={() => handleEdit(r)}>编辑</Button>
          {isAdmin && (
            <Popconfirm title="确定删除该企业吗？" onConfirm={() => handleDelete(r.id)}>
              <Button type="link" size="small" danger>删除</Button>
            </Popconfirm>
          )}
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
        title={editingEnterprise ? '编辑企业' : '新建企业'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={720}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={handleSubmit}>
          {/* 第一组：基本信息 */}
          <Title level={5} style={{ marginTop: 0, marginBottom: 16 }}>基本信息</Title>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="company_code" label="公司代码" rules={[{ required: true, message: '请输入公司代码' }]}>
                <Input maxLength={10} placeholder="股票代码" disabled={!!editingEnterprise} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="company_name" label="公司简称" rules={[{ required: true, message: '请输入公司简称' }]}>
                <Input maxLength={100} placeholder="公司简称" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="english_name" label="英文名称">
                <Input maxLength={200} placeholder="英文名称" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="category_name" label="门类名称" rules={[{ required: true, message: '请选择门类' }]}>
                <Select showSearch allowClear placeholder="选择门类">
                  {categories.map(c => <Option key={c} value={c}>{c}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="industry_code" label="行业代码" rules={[{ required: true, message: '请输入行业代码' }]}>
                <Input maxLength={10} placeholder="行业代码" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="industry_name" label="行业名称" rules={[{ required: true, message: '请选择行业' }]}>
                <Select showSearch allowClear placeholder="选择行业">
                  {industries.map(i => <Option key={i} value={i}>{i}</Option>)}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          {/* 第二组：注册信息 */}
          <Title level={5} style={{ marginBottom: 16 }}>注册信息</Title>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="legal_representative" label="法人代表">
                <Input maxLength={50} placeholder="法人代表" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="registered_capital" label="注册资金">
                <InputNumber
                  min={0}
                  precision={2}
                  style={{ width: '100%' }}
                  placeholder="注册资金"
                  addonAfter="万元"
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="establish_date" label="成立日期">
                <DatePicker style={{ width: '100%' }} placeholder="选择日期" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="listing_date" label="上市日期">
                <DatePicker style={{ width: '100%' }} placeholder="选择日期" />
              </Form.Item>
            </Col>
            <Col span={16}>
              <Form.Item name="registered_address" label="注册地址">
                <Input maxLength={500} placeholder="注册地址" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="office_address" label="办公地址">
                <Input maxLength={500} placeholder="办公地址" />
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          {/* 第三组：联系方式 */}
          <Title level={5} style={{ marginBottom: 16 }}>联系方式</Title>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="phone" label="联系电话">
                <Input maxLength={200} placeholder="联系电话" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="email" label="电子邮箱">
                <Input maxLength={100} placeholder="电子邮箱" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="fax" label="传真">
                <Input maxLength={200} placeholder="传真" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="website" label="官方网站">
                <Input maxLength={200} placeholder="官方网站 URL" />
              </Form.Item>
            </Col>
          </Row>

          <Divider />

          {/* 第四组：经营信息 */}
          <Title level={5} style={{ marginBottom: 16 }}>经营信息</Title>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="main_business" label="主营业务">
                <TextArea rows={3} maxLength={2000} placeholder="主营业务描述" showCount />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="business_scope" label="经营范围">
                <TextArea rows={3} maxLength={2000} placeholder="经营范围" showCount />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={24}>
              <Form.Item name="company_profile" label="机构简介">
                <TextArea rows={3} maxLength={2000} placeholder="机构简介" showCount />
              </Form.Item>
            </Col>
          </Row>

          {/* 底部按钮 */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
            <Button onClick={() => setModalVisible(false)}>取消</Button>
            <Button 
              icon={<SaveOutlined />} 
              onClick={() => form.validateFields().then(values => handleSave(values, false))}
            >
              暂存
            </Button>
            <Button type="primary" onClick={() => form.submit()}>
              保存
            </Button>
          </div>
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
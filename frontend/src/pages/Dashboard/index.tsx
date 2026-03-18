import { useState, useEffect } from 'react'
import { Card, Row, Col, Statistic, Typography, Spin } from 'antd'
import {
  UserOutlined,
  TeamOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons'
import apiClient from '@/lib/api'

const { Title } = Typography

interface Stats {
  userCount: number
  enterpriseCount: number
  reportCount: number
}

function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<Stats>({
    userCount: 0,
    enterpriseCount: 0,
    reportCount: 0,
  })

  const fetchStats = async () => {
    setLoading(true)
    try {
      // 并行获取用户数和企业数
      const [usersRes, enterprisesRes] = await Promise.all([
        apiClient.get('/api/users', { params: { page: 1, page_size: 1 } }),
        apiClient.get('/api/enterprises', { params: { page: 1, page_size: 1 } }),
      ])

      setStats({
        userCount: usersRes.data.total || 0,
        enterpriseCount: enterprisesRes.data.total || 0,
        reportCount: 0, // Phase 4+
      })
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  return (
    <div>
      <Title level={3} style={{ marginBottom: 24 }}>
        仪表盘
      </Title>

      <Spin spinning={loading}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="用户总数"
                value={stats.userCount}
                prefix={<UserOutlined />}
                valueStyle={{ color: '#3f8600' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="企业数量"
                value={stats.enterpriseCount}
                prefix={<TeamOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="诊断报告"
                value={stats.reportCount}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#722ed1' }}
              />
            </Card>
          </Col>

          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="系统状态"
                value="正常"
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
        </Row>
      </Spin>

      <Card style={{ marginTop: 24 }}>
        <Title level={4}>欢迎使用企业健康诊断平台</Title>
        <p>
          本平台提供企业健康度智能诊断服务，支持财务数据分析和定性问卷评价，
          自动生成符合《企业诊断评价报告 V4.0》格式的专业报告。
        </p>
        <ul>
          <li>Phase 1: 核心框架验证 - 用户认证系统 ✅</li>
          <li>Phase 2: 企业数据管理 - 财务数据上传</li>
          <li>Phase 3: 指标计算引擎 - 18项定量指标</li>
          <li>Phase 4: AI报告生成 - Word+PDF导出</li>
          <li>Phase 5: 历史数据与优化</li>
        </ul>
      </Card>
    </div>
  )
}

export default DashboardPage
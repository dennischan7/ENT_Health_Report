import { useState, useEffect } from 'react'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'
import { Layout, Menu, Avatar, Dropdown, Button, Typography, Space } from 'antd'
import {
  DashboardOutlined,
  TeamOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DollarOutlined,
  RobotOutlined,
  SettingOutlined,
} from '@ant-design/icons'

const { Header, Sider, Content } = Layout
const { Text } = Typography

interface MenuItem {
  key: string
  icon?: React.ReactNode
  label: string
  path?: string
  children?: MenuItem[]
}

const menuItems: MenuItem[] = [
  { key: 'dashboard', icon: <DashboardOutlined />, label: '仪表盘', path: '/dashboard' },
  { key: 'enterprises', icon: <TeamOutlined />, label: '企业管理', path: '/enterprises' },
  { key: 'financials', icon: <DollarOutlined />, label: '财务数据', path: '/financials' },
  { key: 'users', icon: <UserOutlined />, label: '用户管理', path: '/users' },
  {
    key: 'ai-analysis',
    icon: <RobotOutlined />,
    label: 'AI分析',
    children: [
      { key: 'ai-config', icon: <SettingOutlined />, label: 'AI配置管理', path: '/ai-config' },
      { key: 'peer-comparison', label: '同行对比分析', path: '/ai-analysis' },
    ],
  },
]

function MainLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      setUser(JSON.parse(userStr))
    }
  }, [])

  const handleMenuClick = (key: string) => {
    // First check flat items
    const flatItem = menuItems.find(m => m.key === key && m.path)
    if (flatItem && flatItem.path) {
      navigate(flatItem.path)
      return
    }
    // Then check submenu items
    for (const item of menuItems) {
      if (item.children) {
        const childItem = item.children.find(c => c.key === key && c.path)
        if (childItem && childItem.path) {
          navigate(childItem.path)
          return
        }
      }
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    navigate('/login')
  }

  const userMenu = (
    <Dropdown
      menu={{
        items: [
          {
            key: 'profile',
            icon: <UserOutlined />,
            label: '个人信息',
          },
          {
            key: 'logout',
            icon: <LogoutOutlined />,
            label: '退出登录',
            danger: true,
            onClick: handleLogout,
          },
        ],
      }}
    >
      <Space style={{ cursor: 'pointer' }}>
        <Avatar icon={<UserOutlined />} />
        <Text>{user?.full_name || user?.email}</Text>
      </Space>
    </Dropdown>
  )

  // Find the current selected key and open parent submenu
  const findCurrentKey = (): string => {
    // Check flat items first
    for (const item of menuItems) {
      if (item.path && location.pathname.startsWith(item.path)) {
        return item.key
      }
    }
    // Check submenu children
    for (const item of menuItems) {
      if (item.children) {
        for (const child of item.children) {
          if (child.path && location.pathname.startsWith(child.path)) {
            return child.key
          }
        }
      }
    }
    return 'dashboard'
  }

  // Find the parent key to open submenu
  const findOpenKey = (key: string): string | undefined => {
    for (const item of menuItems) {
      if (item.children) {
        const found = item.children.find(c => c.key === key)
        if (found) {
          return item.key
        }
      }
    }
    return undefined
  }

  // Calculate current key and open key (must be before useState/useEffect that use them)
  const currentKey = findCurrentKey()
  const openKey = findOpenKey(currentKey)

  const [openKeys, setOpenKeys] = useState<string[]>([])

  // Auto-open submenu on initial load if child is selected
  useEffect(() => {
    if (openKey && !openKeys.includes(openKey)) {
      setOpenKeys([openKey])
    }
  }, [openKey])

  const handleOpenChange = (keys: string[]) => {
    setOpenKeys(keys)
  }

  // Convert menu items to Ant Design menu format
  const getAntdMenuItems = (items: MenuItem[]): any[] => {
    return items.map(item => {
      if (item.children) {
        return {
          key: item.key,
          icon: item.icon,
          label: item.label,
          children: item.children.map(child => ({
            key: child.key,
            icon: child.icon,
            label: child.label,
            onClick: () => handleMenuClick(child.key),
          })),
        }
      }
      return {
        key: item.key,
        icon: item.icon,
        label: item.label,
        onClick: () => handleMenuClick(item.key),
      }
    })
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div
          style={{
            height: 64,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#fff',
            fontSize: collapsed ? 16 : 18,
            fontWeight: 'bold',
          }}
        >
          {collapsed ? '健康' : '企业健康诊断'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[currentKey]}
          openKeys={openKeys}
          onOpenChange={handleOpenChange}
          items={getAntdMenuItems(menuItems)}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: 16 }}
          />
          {userMenu}
        </Header>
        <Content
          style={{
            margin: 24,
            padding: 24,
            background: '#fff',
            borderRadius: 8,
            minHeight: 280,
          }}
        >
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}

export default MainLayout
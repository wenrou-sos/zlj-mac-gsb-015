import { NavLink, Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Trains from './pages/Trains'
import Tracks from './pages/Tracks'
import Locomotives from './pages/Locomotives'
import Rules from './pages/Rules'

const NAV = [
  { to: '/', label: '冲突分析', end: true },
  { to: '/trains', label: '货列管理' },
  { to: '/tracks', label: '股道管理' },
  { to: '/locomotives', label: '机车资源' },
  { to: '/rules', label: '编组规则' },
]

export default function App() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-icon">🚂</span>
          <div>
            <h1>编组冲突分析</h1>
            <p>铁路货运调度平台</p>
          </div>
        </div>
        <nav>
          {NAV.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end}
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/trains" element={<Trains />} />
          <Route path="/tracks" element={<Tracks />} />
          <Route path="/locomotives" element={<Locomotives />} />
          <Route path="/rules" element={<Rules />} />
        </Routes>
      </main>
    </div>
  )
}

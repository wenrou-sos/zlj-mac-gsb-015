import ResourcePage from '../components/ResourcePage'

const fields = [
  { name: 'name', label: '规则名称', type: 'text', required: true },
  { name: 'max_wagons', label: '最大编组辆数', type: 'number', default: 60, required: true },
  { name: 'max_length_m', label: '最大列车长度（米）', type: 'number', default: 850, required: true },
  { name: 'max_weight_t', label: '最大总重（吨）', type: 'number', default: 5000, required: true },
  { name: 'min_departure_interval_min', label: '最小出发间隔（分钟）', type: 'number', default: 15, required: true },
  { name: 'max_dwell_time_min', label: '最大停留时间（分钟）', type: 'number', default: 720, required: true },
  { name: 'is_active', label: '启用', type: 'checkbox', default: true },
]

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: '名称' },
  { key: 'max_wagons', label: '辆数上限' },
  { key: 'max_length_m', label: '长度上限（m）' },
  { key: 'max_weight_t', label: '重量上限（t）' },
  { key: 'min_departure_interval_min', label: '出发间隔（min）' },
  { key: 'max_dwell_time_min', label: '停留上限（min）' },
  { key: 'is_active', label: '状态', render: (r) => (r.is_active ? '✅ 启用' : '停用') },
]

export default function Rules() {
  return <ResourcePage resource="rules" title="编组规则" fields={fields} columns={columns} />
}

import ResourcePage from '../components/ResourcePage'

const fields = [
  { name: 'loco_number', label: '机车编号', type: 'text', required: true },
  {
    name: 'loco_type', label: '机型', type: 'select', default: 'electric',
    options: [
      { value: 'electric', label: '电力机车' },
      { value: 'diesel', label: '内燃机车' },
    ],
  },
  { name: 'max_traction_weight_t', label: '最大牵引重量（吨）', type: 'number', required: true },
  {
    name: 'status', label: '状态', type: 'select', default: 'available',
    options: [
      { value: 'available', label: '可用' },
      { value: 'maintenance', label: '检修中' },
    ],
  },
  { name: 'available_from', label: '可用起始时间', type: 'datetime' },
  { name: 'available_until', label: '可用截止时间', type: 'datetime' },
]

const TYPE_LABEL = { electric: '电力', diesel: '内燃' }
const STATUS_LABEL = { available: '可用', maintenance: '检修中' }
const fmtTime = (v) => (v ? new Date(v).toLocaleString('zh-CN', { hour12: false }) : '—')

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'loco_number', label: '编号' },
  { key: 'loco_type', label: '机型', render: (r) => TYPE_LABEL[r.loco_type] || r.loco_type },
  { key: 'max_traction_weight_t', label: '最大牵引（t）' },
  { key: 'status', label: '状态', render: (r) => STATUS_LABEL[r.status] || r.status },
  { key: 'available_from', label: '可用起始', render: (r) => fmtTime(r.available_from) },
]

export default function Locomotives() {
  return <ResourcePage resource="locomotives" title="机车资源" fields={fields} columns={columns} />
}

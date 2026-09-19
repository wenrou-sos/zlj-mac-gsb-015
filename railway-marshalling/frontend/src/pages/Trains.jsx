import ResourcePage from '../components/ResourcePage'

const fields = [
  { name: 'train_number', label: '车次', type: 'text', required: true },
  { name: 'arrival_time', label: '到达时间', type: 'datetime', required: true },
  { name: 'departure_time', label: '出发时间', type: 'datetime' },
  { name: 'wagon_count', label: '编组辆数', type: 'number', default: 0 },
  { name: 'total_length_m', label: '列车长度（米）', type: 'number', default: 0 },
  { name: 'total_weight_t', label: '总重（吨）', type: 'number', default: 0 },
  { name: 'cargo_type', label: '货物类型', type: 'text', default: 'general' },
  { name: 'priority', label: '优先级（1高-5低）', type: 'number', default: 3 },
  { name: 'track_id', label: '所在股道', type: 'select', optionsSource: 'tracks', optionLabel: 'name' },
  { name: 'locomotive_id', label: '牵引机车', type: 'select', optionsSource: 'locomotives', optionLabel: 'loco_number' },
]

const fmtTime = (v) => (v ? new Date(v).toLocaleString('zh-CN', { hour12: false }) : '未定')

const columns = [
  { key: 'train_number', label: '车次' },
  { key: 'arrival_time', label: '到达', render: (r) => fmtTime(r.arrival_time) },
  { key: 'departure_time', label: '出发', render: (r) => fmtTime(r.departure_time) },
  { key: 'wagon_count', label: '辆数' },
  { key: 'total_length_m', label: '长度（m）' },
  { key: 'total_weight_t', label: '总重（t）' },
  { key: 'cargo_type', label: '货物' },
  { key: 'track_id', label: '股道', render: (r) => r.track_id ?? '—' },
  { key: 'locomotive_id', label: '机车', render: (r) => r.locomotive_id ?? '—' },
]

export default function Trains() {
  return <ResourcePage resource="trains" title="货列管理" fields={fields} columns={columns} />
}

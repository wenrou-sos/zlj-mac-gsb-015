import ResourcePage from '../components/ResourcePage'

const fields = [
  { name: 'name', label: '股道名称', type: 'text', required: true },
  { name: 'length_m', label: '有效长度（米）', type: 'number', required: true },
  {
    name: 'track_type', label: '股道类型', type: 'select', default: 'arrival_departure',
    options: [
      { value: 'arrival_departure', label: '到发线' },
      { value: 'classification', label: '调车线' },
      { value: 'storage', label: '存车线' },
    ],
  },
  {
    name: 'status', label: '状态', type: 'select', default: 'active',
    options: [
      { value: 'active', label: '可用' },
      { value: 'maintenance', label: '维修中' },
    ],
  },
]

const TYPE_LABEL = { arrival_departure: '到发线', classification: '调车线', storage: '存车线' }
const STATUS_LABEL = { active: '可用', maintenance: '维修中' }

const columns = [
  { key: 'id', label: 'ID' },
  { key: 'name', label: '名称' },
  { key: 'length_m', label: '有效长（m）' },
  { key: 'track_type', label: '类型', render: (r) => TYPE_LABEL[r.track_type] || r.track_type },
  { key: 'status', label: '状态', render: (r) => STATUS_LABEL[r.status] || r.status },
]

export default function Tracks() {
  return <ResourcePage resource="tracks" title="股道管理" fields={fields} columns={columns} />
}

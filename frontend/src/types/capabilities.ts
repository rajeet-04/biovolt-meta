export type AccessMode = 'operator' | 'public_read_only'
export interface Capabilities { access_mode: AccessMode; can_control: boolean; can_manage_experiments: boolean; can_manage_calibration: boolean; can_view_live: boolean; can_export: boolean }

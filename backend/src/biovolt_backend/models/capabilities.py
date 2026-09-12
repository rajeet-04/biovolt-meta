from typing import Literal

from pydantic import BaseModel, ConfigDict

AccessMode = Literal["operator", "public_read_only"]


class Capabilities(BaseModel):
    model_config = ConfigDict(frozen=True)
    access_mode: AccessMode
    can_control: bool
    can_manage_experiments: bool
    can_manage_calibration: bool
    can_view_live: bool = True
    can_export: bool = True

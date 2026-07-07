"""
元数据提取模块
===============
从文件中提取嵌入式元数据：
  - EXIF (JPEG/TIFF 图片): 相机型号、GPS、时间戳
  - Office XML (.docx/.xlsx): 作者、创建时间、修改历史
  - PDF: /Info 字典 (作者、创建时间、修改器)
"""

from __future__ import annotations
import struct
import zipfile
import xml.etree.ElementTree as ET
import re
from pathlib import Path
from typing import Any

from forensic_toolkit.core.module_base import ModuleBase, ModuleMeta, ModuleRegistry


# ── EXIF 解析 ─────────────────────────────────────────

_EXIF_ASCII = 2
_EXIF_SHORT = 3
_EXIF_LONG = 4
_EXIF_UNDEFINED = 7
_EXIF_IFD_TAGS = {
    0x010F: "Make",
    0x0110: "Model",
    0x0112: "Orientation",
    0x0132: "DateTimeOriginal",
    0x013B: "Artist",
    0x011A: "XResolution",
    0x011B: "YResolution",
    0x8769: "ExifIFD",
    0x8825: "GPSInfo",
    0xA002: "PixelXDimension",
    0xA003: "PixelYDimension",
    0x9286: "UserComment",
}

_GPS_TAGS = {
    0x0001: "GPSLatitudeRef",
    0x0002: "GPSLatitude",
    0x0003: "GPSLongitudeRef",
    0x0004: "GPSLongitude",
    0x0005: "GPSAltitudeRef",
    0x0006: "GPSAltitude",
    0x0007: "GPSTimeStamp",
    0x0010: "GPSImgDirectionRef",
    0x0011: "GPSImgDirection",
}


def _parse_exif(data: bytes) -> dict:
    """从 JPEG/raw 数据中解析 EXIF TIFF/IFD。"""
    result = {}

    # 查找 EXIF 起始 "Exif\0\0" 或 TIFF header
    pos = data.find(b"Exif\x00\x00")
    if pos == -1:
        return result
    tiff_off = pos + 6

    # TIFF header
    if tiff_off + 8 > len(data):
        return result
    endian = data[tiff_off:tiff_off + 2]
    if endian == b"II":  # Little-endian
        le = True
    elif endian == b"MM":  # Big-endian
        le = False
    else:
        return result

    def _get16(off: int) -> int:
        return struct.unpack("<H" if le else ">H", data[off:off + 2])[0]

    def _get32(off: int) -> int:
        return struct.unpack("<I" if le else ">I", data[off:off + 4])[0]

    def _read_ifd(ifd_off: int, base: int, tag_map: dict) -> dict:
        if ifd_off + 2 > len(data):
            return {}
        out = {}
        count = _get16(base + ifd_off)
        entry_size = 12
        for i in range(count):
            entry_off = base + ifd_off + 2 + i * entry_size
            if entry_off + 12 > len(data):
                break
            tag = _get16(entry_off)
            dtype = _get16(entry_off + 2)
            dcount = _get32(entry_off + 4)
            value_off = entry_off + 8

            tag_name = tag_map.get(tag, f"0x{tag:04X}")
            if tag == 0x8769:  # ExifIFD
                sub = _read_ifd(_get32(value_off), base, _EXIF_IFD_TAGS)
                out.update(sub)
            elif tag == 0x8825:  # GPSInfo
                gps = _read_ifd(_get32(value_off), base, _GPS_TAGS)
                out.update(gps)
            elif dtype == 2 and dcount <= 32:  # ASCII string
                val = data[value_off:value_off + dcount - 1]
                try:
                    out[tag_name] = val.decode("ascii").strip()
                except Exception:
                    pass
            elif dtype in (3, 4, 7):
                val = _get32(value_off)
                out[tag_name] = val
            elif dtype == 5:  # RATIONAL
                num_off = base + _get32(value_off)
                if num_off + 8 <= len(data):
                    num = _get32(num_off)
                    den = _get32(num_off + 4)
                    out[tag_name] = num / den if den else 0
        return out

    magic = _get16(tiff_off + 2)
    if magic != 42:
        return result
    ifd0 = _get32(tiff_off + 4)
    result = _read_ifd(ifd0, tiff_off, _EXIF_IFD_TAGS)
    return result


# ── Office XML 元数据 ─────────────────────────────────

def _parse_office_xml(path: Path) -> dict:
    """从 Office Open XML (docx/xlsx/pptx) 中提取元数据。"""
    result = {}
    try:
        with zipfile.ZipFile(path, "r") as z:
            # docProps/core.xml
            if "docProps/core.xml" in z.namelist():
                xml_data = z.read("docProps/core.xml")
                root = ET.fromstring(xml_data)
                ns = {
                    "dc": "http://purl.org/dc/elements/1.1/",
                    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
                    "dcterms": "http://purl.org/dc/terms/",
                }
                for tag in ("dc:creator", "cp:lastModifiedBy", "dc:title",
                            "dc:description", "dcterms:created", "dcterms:modified"):
                    elem = root.find(tag, ns)
                    if elem is not None and elem.text:
                        result[tag.split(":")[1]] = elem.text.strip()
            # docProps/app.xml
            if "docProps/app.xml" in z.namelist():
                xml_data = z.read("docProps/app.xml")
                root = ET.fromstring(xml_data)
                ns = {"": "http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"}
                for tag in ("Application", "TotalTime", "Pages", "Words", "Characters"):
                    elem = root.find(tag, ns)
                    if elem is not None and elem.text:
                        result[tag] = elem.text.strip()
    except Exception:
        pass
    return result


# ── PDF 元数据 ─────────────────────────────────────────

def _parse_pdf(path: Path) -> dict:
    """从 PDF 中提取 /Info 字典。"""
    result = {}
    try:
        data = path.read_bytes()
        # 查找 /Info 字典
        info_match = re.search(rb"/Info\s*<<(.+?)>>", data, re.DOTALL)
        if info_match:
            info_text = info_match.group(1).decode("latin-1")
            # 提取 /Author, /Title, /Subject, /Creator, /Producer, /CreationDate
            for key in ("Author", "Title", "Subject", "Creator", "Producer", "CreationDate", "ModDate"):
                m = re.search(rf"/{key}\s*\(([^)]*)\)", info_text)
                if m:
                    result[key] = m.group(1).strip()
    except Exception:
        pass
    return result


class MetadataModule(ModuleBase):
    meta = ModuleMeta(
        name="metadata",
        description="提取文件元数据 (EXIF / Office / PDF)",
        author="Forensic Toolkit",
        version="0.1.0",
    )

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._path = Path(self.params["path"])

    def run(self) -> Any:
        path = self._path
        if not path.exists():
            return {"error": f"路径不存在: {path}"}

        ext = path.suffix.lower()
        metadata: dict = {"file": str(path.resolve()), "format": "unknown", "metadata": {}}

        try:
            if ext in (".jpg", ".jpeg", ".tif", ".tiff"):
                metadata["format"] = "EXIF (JPEG/TIFF)"
                metadata["metadata"] = _parse_exif(path.read_bytes())
            elif ext in (".docx", ".xlsx", ".pptx"):
                metadata["format"] = "Office Open XML"
                metadata["metadata"] = _parse_office_xml(path)
            elif ext == ".pdf":
                metadata["format"] = "PDF"
                metadata["metadata"] = _parse_pdf(path)
            else:
                # 尝试魔数猜测
                head = path.read_bytes(512)
                if head[:3] == b"\xff\xd8\xff":
                    metadata["format"] = "JPEG (魔数检测)"
                    metadata["metadata"] = _parse_exif(path.read_bytes(64 * 1024))
                elif head[:4] == b"%PDF":
                    metadata["format"] = "PDF (魔数检测)"
                    metadata["metadata"] = _parse_pdf(path)
                elif head[:4] == b"PK\x03\x04":
                    metadata["format"] = "Office ZIP (魔数检测)"
                    metadata["metadata"] = _parse_office_xml(path)
                else:
                    metadata["note"] = f"不支持的文件类型: {ext}"
        except Exception as e:
            return {"error": str(e), "file": str(path.resolve())}

        return metadata


ModuleRegistry.register(MetadataModule)

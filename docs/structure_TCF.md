# structure of TCF

```bash
HDF5.File
├─ CreateDate
├─ DataID
├─ Description
├─ DeviceHost
├─ DeviceSerial
├─ DeviceSoftwareVersion
├─ FormatVersion
├─ RecordingTime
├─ SoftwareVersion
├─ Title
├─ UniqueID
├─ UserID
├─ Data
│  ├─ 2DMIP
│  │  ├─ DataCount
│  │  ├─ RIMax
│  │  ├─ RIMin
│  │  ├─ ResolutionX
│  │  ├─ ResolutionY
│  │  ├─ SizeX
│  │  ├─ SizeY
│  │  ├─ TimeInterval
│  │  └─ 000000
│  │     ├─ PositionC
│  │     ├─ PositionX
│  │     ├─ PositionY
│  │     ├─ PositionZ
│  │     ├─ RIMax
│  │     ├─ RIMin
│  │     ├─ RecordingTime
│  │     └─ Time
│  ├─ 3D
│  │  ├─ DataCount
│  │  ├─ RIMax
│  │  ├─ RIMin
│  │  ├─ ResolutionX
│  │  ├─ ResolutionY
│  │  ├─ ResolutionZ
│  │  ├─ SizeX
│  │  ├─ SizeY
│  │  ├─ SizeZ
│  │  ├─ TimeInterval
│  │  └─ 000000
│  │     ├─ PositionC
│  │     ├─ PositionX
│  │     ├─ PositionY
│  │     ├─ PositionZ
│  │     ├─ RIMax
│  │     ├─ RIMin
│  │     ├─ RecordingTime
│  │     └─ Time
│  └─ BF
│     ├─ DataCount
│     ├─ ResolutionX
│     ├─ ResolutionY
│     ├─ SizeX
│     ├─ SizeY
│     ├─ TimeInterval
│     └─ 000000
│        ├─ PositionC
│        ├─ PositionX
│        ├─ PositionY
│        ├─ PositionZ
│        ├─ RecordingTime
│        └─ Time
└─ Info
   ├─ Annotation
   ├─ Device
   │  ├─ Iteration
   │  ├─ Magnification
   │  ├─ NA
   │  ├─ RI
   │  ├─ Rawsize
   │  ├─ Wavelength
   │  ├─ ZP
   │  ├─ ZP2
   │  └─ ZP3
   └─ Imaging
      ├─ CameraGain
      └─ CameraShutter
```

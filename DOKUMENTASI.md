# 📄 Dokumentasi Aplikasi PO Approval System

> **Untuk siapa dokumen ini?**
> Dokumen ini ditulis untuk siapa saja — bahkan yang belum pernah belajar pemrograman sekalipun — agar bisa memahami apa yang dilakukan aplikasi ini dan konsep-konsep pemrograman yang digunakan di dalamnya.

---

## 🏢 Apa Itu Aplikasi Ini?

Bayangkan kamu bekerja di sebuah kantor. Suatu hari kamu butuh membeli kursi baru untuk ruangannya. Kamu tidak bisa langsung pergi ke toko dan membeli sendiri menggunakan uang kantor — kamu harus **meminta izin dulu ke atasan**.

Itulah yang disimulasikan oleh aplikasi ini: sebuah sistem persetujuan pembelian barang (dalam dunia kerja disebut **Purchase Order** atau disingkat **PO**).

### Siapa saja yang terlibat?

| Peran | Tugasnya |
|---|---|
| **Requester** (Pemohon) | Karyawan yang mengajukan permintaan pembelian barang |
| **Manager** (Atasan) | Orang yang berwenang menyetujui atau menolak permintaan tersebut |

---

## 🔄 Bagaimana Alur Kerjanya?

Setiap permintaan pembelian melewati beberapa tahapan, seperti sebuah perjalanan:

```
[DRAFT] ──► [MENUNGGU PERSETUJUAN] ──► [DISETUJUI] ──► [SELESAI]
                        │
                        └──► [DITOLAK]
```

Penjelasan tiap tahap:

1. **DRAFT** — Karyawan mengisi formulir permintaan (nama barang, jumlah, harga perkiraan) lalu menyimpannya sebagai draf. Ibarat menulis surat tapi belum dikirim.

2. **MENUNGGU PERSETUJUAN (PENDING APPROVAL)** — Karyawan menekan tombol "kirim". Surat sudah di tangan atasan dan menunggu keputusan.

3. **DISETUJUI (APPROVED)** — Atasan menyetujui permintaan. Sistem otomatis membuat nomor PO resmi.

4. **SELESAI (COMPLETED)** — Dokumen PO resmi sudah diterbitkan. Proses selesai.

5. **DITOLAK (REJECTED)** — Atasan menolak permintaan dan wajib memberikan alasan penolakan.

### Notifikasi Otomatis

Setiap kali ada perubahan status, aplikasi secara otomatis mengirimkan notifikasi kepada pihak yang berkepentingan:
- Ketika PO dikirim → Manajer mendapat notifikasi bahwa ada permintaan baru.
- Ketika PO disetujui/ditolak → Pemohon mendapat notifikasi tentang keputusan atasannya.

---

## 🧱 Konsep Pemrograman yang Digunakan

Bagian ini menjelaskan konsep-konsep pemrograman yang diterapkan dalam aplikasi, dengan analogi kehidupan sehari-hari agar lebih mudah dipahami.

---

### 1. 🏛️ OOP (Pemrograman Berorientasi Objek)

OOP adalah cara membuat program dengan meniru cara kerja dunia nyata: dunia nyata penuh dengan **objek** (benda), dan setiap objek punya **sifat** dan **kemampuan**.

---

#### 📦 Class dan Object

- **Class** adalah **cetakan** atau **blueprint**. Contoh: cetakan kue berbentuk bintang.
- **Object** adalah **hasil cetakannya** yang nyata. Contoh: kue bintang yang sudah jadi.

Dalam aplikasi ini:

```
Class PurchaseOrder  →  Cetakan/template sebuah dokumen permintaan pembelian
Object po1           →  Permintaan pembelian "Kursi Kantor" milik Budi
Object po2           →  Permintaan pembelian "Laptop" milik Siti
```

Kode yang relevan: `models/purchase_order.py`
```python
class PurchaseOrder:          # <-- ini CETAKAN-nya
    def __init__(self, requester, item_name, ...):
        self.requester = requester   # sifat: siapa yang minta
        self.item_name = item_name   # sifat: nama barang
        self.quantity  = quantity    # sifat: jumlah
        ...
```

---

#### 🔒 Enkapsulasi (Encapsulation)

**Enkapsulasi** artinya menyembunyikan detail "jeroan" dari luar, hanya memperlihatkan yang perlu saja.

Analogi: mesin mobil ada di dalam kap — pengemudi tidak perlu tahu cara kerja pistonnya, cukup tekan pedal gas.

Dalam aplikasi ini, objek PurchaseOrder menyembunyikan caranya berpindah status menggunakan atribut `_state` (diawali `_` sebagai tanda "privat"):

```python
self._state = DraftState()   # detail internal, tidak perlu diketahui dari luar
```

Dari luar, kita cukup memanggil metode yang disediakan:

```python
po.submit()    # "kirim PO" — tanpa perlu tahu bagaimana proses di dalamnya
po.approve()   # "setujui PO"
po.reject()    # "tolak PO"
```

---

#### 🧬 Pewarisan (Inheritance)

**Pewarisan** artinya sebuah class "mewarisi" sifat dan kemampuan dari class induknya, persis seperti anak yang mewarisi ciri orang tuanya.

Analogi: Semua kendaraan punya kemampuan "bergerak". Mobil dan Motor mewarisi kemampuan itu, lalu masing-masing menambahkan kemampuan uniknya sendiri.

Dalam aplikasi ini, setiap status PO adalah sebuah class yang mewarisi class induk `POState`:

```
POState (induk)
    ├── DraftState           (status: DRAFT)
    ├── PendingApprovalState (status: MENUNGGU PERSETUJUAN)
    ├── ApprovedState        (status: DISETUJUI)
    ├── RejectedState        (status: DITOLAK)
    └── CompletedState       (status: SELESAI)
```

Kode yang relevan: `models/po_states.py`
```python
class POState(ABC):          # <-- class INDUK
    ...

class DraftState(POState):   # <-- class ANAK, mewarisi POState
    ...
```

---

#### 🎭 Abstraksi (Abstraction)

**Abstraksi** artinya mendefinisikan sebuah "kontrak" atau aturan umum yang wajib diikuti, tanpa menentukan detailnya. Mirip peraturan: "Setiap karyawan wajib memakai seragam" — aturannya sama, tapi wujud seragamnya bisa berbeda tiap departemen.

Dalam aplikasi ini, `POState` adalah class abstrak yang mewajibkan setiap status untuk mendefinisikan properti `status`-nya sendiri:

```python
class POState(ABC):               # ABC = Abstract Base Class
    @property
    @abstractmethod
    def status(self) -> StatusEnum:   # WAJIB diisi oleh class turunan
        pass
```

Setiap class status turunan (DraftState, ApprovedState, dll.) **wajib** mengisi `status` ini dengan nilai yang sesuai.

---

#### 🦆 Polimorfisme (Polymorphism)

**Polimorfisme** artinya satu perintah yang sama bisa menghasilkan perilaku berbeda tergantung siapa yang menerimanya.

Analogi: Kamu bilang "Nyanyikan lagu!" kepada penyanyi jazz dan penyanyi dangdut — keduanya menyanyi, tapi lagunya berbeda.

Dalam aplikasi ini, metode `submit()` dipanggil dari objek PO, tapi hasilnya bergantung pada status PO saat ini:

```python
# Jika PO berstatus DRAFT: berhasil pindah ke PENDING_APPROVAL
po.submit()

# Jika PO berstatus APPROVED: ERROR karena tidak boleh submit ulang
po.submit()
```

Perintahnya sama (`submit()`), tapi perilakunya berbeda karena ditangani oleh class state yang berbeda.

---

### 2. 📂 Modularitas (Modularity)

**Modularitas** artinya memecah program besar menjadi bagian-bagian kecil yang masing-masing punya tugas spesifik. Persis seperti sebuah toko yang punya bagian kasir, bagian gudang, dan bagian pelayanan — masing-masing bekerja sendiri tapi saling mendukung.

Berikut struktur folder aplikasi ini:

```
uas-oop-sem2-a/
│
├── app.py                  ← "Resepsionis" — menerima permintaan dari web
│
├── models/                 ← "Bagian Operasional" — otak bisnis aplikasi
│   ├── __init__.py         ← Daftar isi: apa saja yang bisa diakses dari folder ini
│   ├── purchase_order.py   ← Definisi "dokumen PO"
│   ├── po_states.py        ← Aturan tiap status (DRAFT, APPROVED, dll.)
│   └── workflow_engine.py  ← Mesin penggerak seluruh alur kerja
│
├── templates/
│   └── index.html          ← Tampilan halaman web (antarmuka pengguna)
│
└── static/
    ├── css/style.css       ← Gaya/desain halaman (warna, font, dll.)
    └── js/app.js           ← Logika interaktif di sisi browser
```

Keuntungan struktur ini:
- **Mudah dicari** — kalau ada masalah pada tampilan, langsung ke folder `templates` atau `static`.
- **Mudah diubah** — mengubah logika status PO cukup di `po_states.py` tanpa menyentuh file lain.
- **Mudah dikembangkan** — ingin menambah fitur baru? Tinggal buat file/modul baru tanpa merusak yang lama.

---

### 3. 🎨 Design Pattern (Pola Desain)

**Design Pattern** adalah "resep masak" yang sudah terbukti berhasil untuk memecahkan masalah tertentu dalam pemrograman. Daripada menemukan cara sendiri dari nol, programmer menggunakan pola yang sudah teruji ini.

Aplikasi ini menggunakan tiga pola desain:

---

#### 🔁 State Pattern (Pola Status)

**Masalah yang dipecahkan:** Bagaimana cara membuat objek yang perilakunya berubah tergantung kondisinya saat ini?

**Analogi:** Lampu lalu lintas. Ketika lampu merah → kendaraan berhenti. Ketika lampu hijau → kendaraan jalan. Perintahnya sama ("apa yang harus dilakukan?"), tapi jawabannya berbeda tergantung warna lampu.

**Dalam aplikasi ini:** Setiap status PO (DRAFT, PENDING, dll.) direpresentasikan sebagai objek terpisah yang "mengambil alih" perilaku PO ketika status itu aktif.

```
PO berstatus DRAFT    → hanya bisa "submit"
PO berstatus PENDING  → hanya bisa "approve" atau "reject"
PO berstatus APPROVED → sistem otomatis "complete"
PO berstatus REJECTED → tidak bisa melakukan apa-apa lagi
PO berstatus COMPLETED → tidak bisa melakukan apa-apa lagi
```

Jika kamu mencoba melakukan aksi yang tidak diizinkan (misalnya menyetujui PO yang masih DRAFT), aplikasi akan langsung memberikan pesan error yang jelas.

File terkait: `models/po_states.py`

---

#### 👑 Singleton Pattern (Pola Satu Instansi)

**Masalah yang dipecahkan:** Bagaimana memastikan hanya ada satu "otak" yang mengelola seluruh data?

**Analogi:** Sebuah perusahaan hanya boleh punya satu direktur utama. Tidak boleh ada dua orang yang sama-sama menjabat sebagai direktur utama karena akan menimbulkan kebingungan dan data yang tidak sinkron.

**Dalam aplikasi ini:** `WorkflowEngine` adalah "direktur utama" aplikasi — hanya boleh ada satu. Tidak peduli berapa kali kita memanggilnya, yang dikembalikan selalu objek yang sama persis.

```python
class WorkflowEngine:
    _instance = None   # tempat menyimpan satu-satunya instansi

    def __new__(cls):
        if cls._instance is None:        # kalau belum ada...
            cls._instance = super().__new__(cls)  # baru dibuat
        return cls._instance             # kembalikan yang sudah ada
```

Manfaatnya: semua data PO tersimpan di satu tempat yang sama, tidak ada duplikasi atau inkonsistensi data.

File terkait: `models/workflow_engine.py`

---

#### 👀 Observer Pattern (Pola Pengamat)

**Masalah yang dipecahkan:** Bagaimana cara memberitahu banyak pihak secara otomatis ketika sesuatu terjadi, tanpa harus "mengawal" satu per satu?

**Analogi:** Bayangkan kamu berlangganan newsletter sebuah toko. Setiap kali toko itu punya promo baru, kamu otomatis dapat email — tanpa harus rajin-rajin mengecek website toko tersebut.

**Dalam aplikasi ini:**
- `WorkflowEngine` bertindak sebagai **"penerbit berita"** — setiap kali status PO berubah, ia mengumumkan kejadian tersebut.
- `NotificationService` bertindak sebagai **"pelanggan"** — ia mendengarkan pengumuman dan menyimpannya sebagai notifikasi.

```
WorkflowEngine                NotificationService
     │                               │
     │  "PO baru disubmit!"  ───────►│  Simpan notifikasi untuk Manajer
     │  "PO disetujui!"      ───────►│  Simpan notifikasi untuk Pemohon
     │  "PO ditolak!"        ───────►│  Simpan notifikasi untuk Pemohon
```

Keuntungannya: jika suatu saat kita ingin menambah fitur pengiriman email atau SMS, cukup tambahkan "pelanggan" baru tanpa mengubah kode `WorkflowEngine` sama sekali.

File terkait: `models/workflow_engine.py`

---

## 🗺️ Peta Hubungan Antar Komponen

Berikut gambaran besar bagaimana semua bagian aplikasi saling terhubung:

```
Pengguna (Browser)
      │
      │  klik tombol / isi form
      ▼
  app.py  (Resepsionis / REST API)
      │
      │  meneruskan permintaan
      ▼
WorkflowEngine  ─── Singleton: hanya satu ───  Menyimpan semua data PO
      │
      ├──► PurchaseOrder  ─── State Pattern ───  Mengelola status & data PO
      │         │
      │         └──► POState (DraftState / PendingApprovalState / ...)
      │
      └──► NotificationService  ─── Observer Pattern ───  Menyimpan notifikasi
```

---

## 📌 Ringkasan

| Konsep | Di mana? | Analogi Sederhana |
|---|---|---|
| **Class & Object** | `PurchaseOrder`, `WorkflowEngine` | Cetakan kue dan kue jadinya |
| **Enkapsulasi** | `_state`, `_pos` (atribut privat) | Mesin mobil tersembunyi di balik kap |
| **Pewarisan** | `DraftState`, `ApprovedState`, dll. mewarisi `POState` | Anak mewarisi ciri orang tua |
| **Abstraksi** | `POState(ABC)`, `WorkflowObserver(ABC)` | Aturan seragam tanpa menentukan modelnya |
| **Polimorfisme** | `po.submit()` berperilaku beda di tiap status | "Nyanyikan lagu!" ke penyanyi yang berbeda |
| **Modularitas** | Folder `models/`, `templates/`, `static/` | Departemen berbeda dalam satu perusahaan |
| **State Pattern** | `po_states.py` | Lampu lalu lintas |
| **Singleton Pattern** | `WorkflowEngine` | Direktur utama yang hanya satu |
| **Observer Pattern** | `NotificationService` | Berlangganan newsletter |

---

*Dokumentasi ini dibuat untuk memudahkan pemahaman konsep pemrograman berorientasi objek melalui contoh nyata dalam kehidupan kantor.*

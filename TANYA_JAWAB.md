# ❓ Tanya Jawab — PO Approval System

Dokumen ini berisi kumpulan pertanyaan dan jawaban seputar aplikasi dan konsep pemrograman yang digunakan, khususnya **Pemrograman Berorientasi Objek (OOP)**. Cocok digunakan untuk bahan belajar atau persiapan presentasi.

---

## 🏢 Pertanyaan Umum tentang Aplikasi

---

**1. Apa yang dilakukan aplikasi ini secara sederhana?**

Aplikasi ini adalah sistem untuk mengajukan dan menyetujui permintaan pembelian barang di kantor. Seorang karyawan (Requester) bisa membuat permintaan, mengirimkannya ke atasan (Manager), dan atasan bisa menyetujui atau menolaknya. Semua prosesnya tercatat secara otomatis.

---

**2. Apa saja tahapan yang dilalui sebuah permintaan pembelian (PO)?**

Sebuah PO melewati tahapan berikut secara berurutan:

```
DRAFT  →  PENDING APPROVAL  →  APPROVED  →  COMPLETED
                    ↓
                 REJECTED
```

- **DRAFT**: Permintaan baru disimpan, belum dikirim.
- **PENDING APPROVAL**: Permintaan sudah dikirim, menunggu keputusan atasan.
- **APPROVED**: Atasan menyetujui.
- **COMPLETED**: Sistem menerbitkan nomor PO resmi secara otomatis.
- **REJECTED**: Atasan menolak dan memberikan alasan.

---

**3. Mengapa penolakan PO harus disertai alasan?**

Karena penolakan tanpa alasan tidak adil bagi pemohon. Ia tidak akan tahu apa yang perlu diperbaiki atau mengapa permintaannya ditolak. Aplikasi ini mewajibkan alasan penolakan dengan cara melakukan validasi — jika alasan kosong, sistem langsung menolak aksi tersebut dengan pesan error:

> *"A rejection reason must be provided."*

Kode validasi ini ada di `models/po_states.py`, di dalam class `PendingApprovalState`, metode `reject()`.

---

**4. Bagaimana notifikasi bekerja di aplikasi ini?**

Setiap kali status PO berubah, sistem secara otomatis membuat notifikasi dan mengirimkannya ke pihak yang tepat:

- PO dikirim → notifikasi masuk ke **Manajer**
- PO disetujui → notifikasi masuk ke **Pemohon**
- PO ditolak → notifikasi masuk ke **Pemohon**

Notifikasi ini tersimpan di dalam memori dan bisa dilihat melalui ikon lonceng di pojok kanan atas antarmuka aplikasi.

---

**5. Apa keuntungan memisahkan kode ke dalam beberapa file/folder (modularitas)?**

Dengan memisahkan kode berdasarkan tanggung jawabnya:

- **Mudah dicari** — kalau ada bug di tampilan, langsung buka `templates/` atau `static/`. Kalau ada masalah logika bisnis, buka `models/`.
- **Mudah diubah** — mengubah aturan status PO cukup di `po_states.py` tanpa khawatir merusak tampilan.
- **Mudah dikembangkan** — ingin tambah fitur notifikasi email? Cukup buat class observer baru, tidak perlu ubah `WorkflowEngine`.

---

## 🧱 Pertanyaan tentang OOP

---

**6. Di bagian mana kamu menerapkan konsep Class dan Object?**

**Class** diterapkan di seluruh file `models/`. Beberapa contohnya:

| Class | File | Fungsinya |
|---|---|---|
| `PurchaseOrder` | `purchase_order.py` | Cetakan untuk setiap dokumen PO |
| `WorkflowEngine` | `workflow_engine.py` | Cetakan untuk mesin penggerak alur kerja |
| `DraftState` | `po_states.py` | Cetakan untuk perilaku PO saat berstatus DRAFT |

**Object** adalah hasil instansiasi (pembuatan) dari class tersebut. Contoh nyata:

```python
# Di workflow_engine.py, saat pengguna membuat PO baru:
po = PurchaseOrder(requester="Budi", item_name="Kursi", ...)
# "po" di atas adalah sebuah OBJECT dari class PurchaseOrder
```

Setiap kali pengguna menekan tombol "Save as Draft", satu object `PurchaseOrder` baru terbentuk di memori.

---

**7. Di bagian mana kamu menerapkan Enkapsulasi? Apa tanda-tandanya?**

Enkapsulasi terlihat jelas di dua tempat:

**a. Atribut privat dengan awalan underscore (`_`)**

```python
# Di purchase_order.py
self._state = DraftState()   # privat: tidak boleh diubah sembarangan dari luar

# Di workflow_engine.py
self._pos = {}               # privat: tempat menyimpan semua data PO
self._observers = [...]      # privat: daftar pengamat
```

Awalan `_` adalah konvensi Python yang artinya: *"ini bagian dalam, jangan diutak-atik dari luar."*

**b. Metode publik sebagai "pintu masuk" resmi**

Alih-alih mengubah `_state` langsung, pihak luar hanya boleh memanggil metode resmi:

```python
po.submit()    # bukan: po._state = PendingApprovalState()
po.approve()
po.reject()
```

Ini menjamin bahwa perubahan status selalu melalui validasi yang benar.

---

**8. Di bagian mana kamu menerapkan Pewarisan (Inheritance)?**

Pewarisan diterapkan di dua tempat dalam folder `models/`:

**a. Hierarki status PO — file `po_states.py`**

```
POState  (class induk / parent)
  ├── DraftState
  ├── PendingApprovalState
  ├── ApprovedState
  ├── RejectedState
  └── CompletedState
```

Kelima class di bawah mewarisi `POState`. Artinya mereka semua mendapatkan metode `submit()`, `approve()`, `reject()`, dan `complete()` secara gratis dari induknya. Masing-masing hanya perlu *menimpa (override)* metode yang relevan untuk statusnya.

**b. Hierarki observer — file `workflow_engine.py`**

```
WorkflowObserver  (class induk)
  └── NotificationService  (class anak)
```

`NotificationService` mewarisi `WorkflowObserver` dan mengimplementasikan metode `on_event()`.

---

**9. Di bagian mana kamu menerapkan Abstraksi? Mengapa perlu diabstraksikan?**

Abstraksi diterapkan menggunakan **Abstract Base Class (ABC)** dari Python, di dua tempat:

**a. `POState` di `po_states.py`**

```python
from abc import ABC, abstractmethod

class POState(ABC):
    @property
    @abstractmethod
    def status(self) -> StatusEnum:
        pass   # <-- tidak ada implementasi, hanya "kontrak"
```

`POState` tidak bisa dibuat objeknya secara langsung. Ia hanya berperan sebagai kontrak: *"Siapa pun yang mengaku sebagai 'state PO' WAJIB punya properti `status`."*

**b. `WorkflowObserver` di `workflow_engine.py`**

```python
class WorkflowObserver(ABC):
    @abstractmethod
    def on_event(self, event, po, message):
        pass   # <-- wajib diimplementasikan oleh class turunan
```

**Mengapa perlu?** Tanpa abstraksi, tidak ada jaminan bahwa semua state atau semua observer punya perilaku yang diharapkan. Abstraksi memaksa programmer mengikuti "kontrak" yang sudah disepakati.

---

**10. Di bagian mana kamu menerapkan Polimorfisme? Berikan contoh nyatanya.**

Polimorfisme paling jelas terlihat saat memanggil metode di objek `PurchaseOrder`:

```python
po.submit()
```

Perintah ini **sama persis** untuk semua PO, tapi hasilnya berbeda tergantung status PO saat ini:

| Status PO saat `submit()` dipanggil | Yang terjadi |
|---|---|
| DRAFT | Berhasil → pindah ke PENDING_APPROVAL |
| PENDING_APPROVAL | Error: *"Cannot submit a PO that is in 'PENDING_APPROVAL' status."* |
| APPROVED | Error: *"Cannot submit a PO that is in 'APPROVED' status."* |
| REJECTED | Error: *"Cannot submit a PO that is in 'REJECTED' status."* |
| COMPLETED | Error: *"Cannot submit a PO that is in 'COMPLETED' status."* |

Hal ini terjadi karena setiap class state mengimplementasikan (atau mewarisi) metode `submit()` secara berbeda. Inilah polimorfisme: **satu antarmuka, banyak perilaku**.

---

**11. Di bagian mana kamu menerapkan Design Pattern Observer? Jelaskan siapa publisher dan siapa subscriber-nya.**

Observer Pattern diterapkan di `models/workflow_engine.py`.

- **Publisher (yang menerbitkan berita):** `WorkflowEngine`
  - Menyimpan daftar observer di `self._observers`
  - Memanggil `self._notify(event, po, message)` setiap kali ada perubahan status PO

- **Subscriber (yang mendengarkan berita):** `NotificationService`
  - Mendaftar sebagai observer di saat `WorkflowEngine` diinisialisasi
  - Menerima event melalui metode `on_event()` dan menyimpannya sebagai notifikasi

Alurnya:
```
WorkflowEngine._notify("PO_SUBMITTED", po, "...")
      │
      └──► NotificationService.on_event("PO_SUBMITTED", po, "...")
                  └──► Simpan notifikasi ke self._store
```

Jika di masa depan ingin menambahkan fitur kirim email, cukup buat class baru:

```python
class EmailNotifier(WorkflowObserver):
    def on_event(self, event, po, message):
        send_email(...)  # logika kirim email

engine.register_observer(EmailNotifier())
```

`WorkflowEngine` tidak perlu diubah sama sekali.

---

**12. Di bagian mana kamu menerapkan Design Pattern Singleton? Mengapa penting?**

Singleton diterapkan pada class `WorkflowEngine` di `models/workflow_engine.py`.

Mekanismenya menggunakan method `__new__` yang merupakan method spesial Python untuk mengontrol pembuatan objek:

```python
class WorkflowEngine:
    _instance = None  # menyimpan satu-satunya instansi

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)  # buat hanya jika belum ada
        return cls._instance  # selalu kembalikan yang sudah ada
```

**Mengapa penting?** Semua data PO disimpan di dalam `WorkflowEngine` (`self._pos`). Jika ada dua instansi `WorkflowEngine`, data PO bisa "terpecah" di dua tempat berbeda dan aplikasi akan memberikan hasil yang tidak konsisten. Singleton menjamin **satu sumber kebenaran**.

---

**13. Di bagian mana kamu menerapkan Design Pattern State? Apa masalah yang dipecahkannya?**

State Pattern diterapkan melalui kerja sama antara `models/purchase_order.py` dan `models/po_states.py`.

**Masalah yang dipecahkan:** Tanpa State Pattern, kode akan penuh dengan blok `if-else` yang panjang dan rapuh:

```python
# Cara TANPA State Pattern (buruk):
def submit(self):
    if self.status == "DRAFT":
        self.status = "PENDING_APPROVAL"
    elif self.status == "PENDING_APPROVAL":
        raise Error("sudah pending")
    elif self.status == "APPROVED":
        raise Error("sudah approved")
    elif ...  # terus bertambah setiap ada status baru
```

**Dengan State Pattern**, setiap status punya "ruangannya" sendiri:

```python
# Cara DENGAN State Pattern (baik):
class DraftState(POState):
    def submit(self, po):
        po._transition_to(PendingApprovalState())  # hanya DraftState yang bisa submit

class PendingApprovalState(POState):
    def submit(self, po):
        raise WorkflowError("...")  # dilarang!
```

Menambah status baru? Cukup buat class baru tanpa menyentuh class lain.

---

**14. Apa perbedaan antara Abstraksi dan Enkapsulasi? Berikan contoh dari kode proyek ini.**

Keduanya sering membingungkan. Bedanya:

| | Abstraksi | Enkapsulasi |
|---|---|---|
| **Tujuan** | Menyembunyikan *kerumitan implementasi* dengan membuat "kontrak" | Menyembunyikan *data internal* agar tidak diakses sembarangan |
| **Fokus** | "Apa yang bisa dilakukan?" | "Bagaimana caranya tersembunyi" |

**Contoh Abstraksi** di proyek ini:

```python
class POState(ABC):
    @abstractmethod
    def status(self): pass   # hanya mendefinisikan "APA" tanpa "BAGAIMANA"
```

Pengguna `POState` tahu ia punya properti `status`, tapi tidak perlu tahu bagaimana cara tiap state mengimplementasikannya.

**Contoh Enkapsulasi** di proyek ini:

```python
class PurchaseOrder:
    def __init__(self):
        self._state = DraftState()  # tersembunyi

    def submit(self):
        self._state.submit(self)    # cara kerjanya tersembunyi
```

Data `_state` disembunyikan; pengguna hanya tahu cara memanggil `submit()`.

---

**15. Bagaimana cara `PurchaseOrder` berpindah dari satu status ke status lain?**

`PurchaseOrder` mendelegasikan semua aksi ke objek `_state`-nya. Ketika state menentukan transisi harus terjadi, ia memanggil method internal `_transition_to()`:

```python
# Di dalam DraftState.submit():
def submit(self, po):
    # ... validasi ...
    po._transition_to(PendingApprovalState())  # ganti state ke pending
    po._add_history("DRAFT → PENDING_APPROVAL", "...")
```

`_transition_to()` hanya mengganti referensi `self._state` ke objek state baru dan memperbarui `updated_at`. Sangat sederhana, tapi efektif.

---

**16. Apa yang terjadi jika kita mencoba menyetujui PO yang masih berstatus DRAFT?**

Aplikasi akan menolak dengan pesan error yang jelas. Ini adalah hasil dari Enkapsulasi dan State Pattern bekerja bersama.

Alurnya:
1. `engine.approve(po_id, manager)` dipanggil
2. `WorkflowEngine` memanggil `po.approve(manager)`
3. `PurchaseOrder.approve()` mendelegasikan ke `self._state.approve()`
4. `self._state` saat ini adalah `DraftState`
5. `DraftState` **tidak** mengoverride metode `approve()`, sehingga menggunakan implementasi default dari class induk `POState`:

```python
def approve(self, po, manager):
    raise WorkflowError(
        f"Cannot approve a Purchase Order that is in 'DRAFT' status."
    )
```

6. Error ini "naik" ke `app.py` dan dikembalikan ke pengguna sebagai respons HTTP 400 dengan pesan error tersebut.

---

**17. Mengapa `WorkflowObserver` dibuat sebagai class abstrak, bukan class biasa?**

Karena kita ingin **memaksa** setiap observer untuk mengimplementasikan metode `on_event()`. Jika dibuat sebagai class biasa (tanpa `@abstractmethod`), programmer bisa saja lupa mengisi `on_event()` dan tidak ada yang memberitahu mereka — sampai terjadi bug di runtime.

Dengan `ABC` dan `@abstractmethod`:

```python
class WorkflowObserver(ABC):
    @abstractmethod
    def on_event(self, event, po, message):
        pass
```

Jika ada yang mencoba membuat class observer tanpa mengisi `on_event()`, Python akan langsung melempar error saat class tersebut di-instansiasi:

> *TypeError: Can't instantiate abstract class MyObserver with abstract method on_event*

Ini adalah bentuk **fail-fast**: lebih baik error terjadi lebih awal saat pengembangan daripada diam-diam gagal saat digunakan.

---

**18. Apa peran `models/__init__.py` dalam konsep modularitas?**

File `__init__.py` berfungsi sebagai **"daftar isi"** atau **"pintu depan"** dari folder `models/`. Ia menentukan apa saja yang boleh diakses dari luar folder tersebut:

```python
# models/__init__.py
from .purchase_order import PurchaseOrder
from .workflow_engine import WorkflowEngine
from .po_states import WorkflowError

__all__ = ["PurchaseOrder", "WorkflowEngine", "WorkflowError"]
```

Berkat ini, `app.py` bisa mengimpor dengan cara yang bersih:

```python
from models import WorkflowEngine, WorkflowError
# bukan: from models.workflow_engine import WorkflowEngine
```

Jika suatu saat struktur file di dalam `models/` diubah (misalnya `workflow_engine.py` dipecah menjadi dua file), `app.py` tidak perlu diubah selama `__init__.py` tetap mengekspor nama yang sama.

---

**19. Bagaimana cara menambahkan jenis notifikasi baru (misalnya notifikasi via email) ke aplikasi ini tanpa mengubah banyak kode?**

Cukup buat class baru yang mewarisi `WorkflowObserver`, lalu daftarkan ke engine:

```python
# File baru: models/email_notifier.py
class EmailNotifier(WorkflowObserver):
    def on_event(self, event, po, message):
        # logika kirim email ke sini
        send_email(to=po.requester, subject=event, body=message)
```

```python
# Di app.py atau inisialisasi aplikasi:
engine.register_observer(EmailNotifier())
```

Tidak ada satu baris pun kode di `WorkflowEngine`, `PurchaseOrder`, atau file lain yang perlu diubah. Inilah keindahan Observer Pattern yang dikombinasikan dengan Abstraksi.

---

**20. Secara keseluruhan, apa manfaat terbesar menggunakan OOP dan Design Pattern dalam proyek ini dibandingkan menulis semua kode di satu file?**

Jika semua kode ditulis di satu file tanpa OOP:
- Kode akan sangat panjang dan sulit dibaca
- Mengubah satu bagian berisiko merusak bagian lain
- Sulit dikerjakan oleh lebih dari satu orang secara bersamaan
- Logika status PO akan jadi satu blok `if-else` besar yang mudah salah

Dengan OOP dan Design Pattern:
- **Setiap class punya satu tanggung jawab** — mudah dimengerti dan diuji
- **Perubahan terisolasi** — mengubah cara notifikasi tidak menyentuh logika PO
- **Kode bisa digunakan ulang** — class observer bisa dipakai di proyek lain
- **Aturan terpaksa diikuti** — abstraksi mencegah programmer membuat class yang "setengah jadi"

Singkatnya: OOP dan Design Pattern membuat kode seperti **mesin yang tersusun dari komponen-komponen**, bukan **gumpalan benang yang kusut**.

---

*Dokumen ini adalah bagian dari seri dokumentasi proyek PO Approval System. Lihat juga [DOKUMENTASI.md](./DOKUMENTASI.md) untuk penjelasan konsep yang lebih lengkap.*

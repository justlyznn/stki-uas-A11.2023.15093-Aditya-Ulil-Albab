import streamlit as st
import pandas as pd
import re
import numpy as np

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('E:\KULIAH\SMST 5\STKI\Pantai_karimun\data\labelling\label_data.csv')
    return df

df = load_data()

# Fungsi preprocessing untuk pencarian
def preprocess_text(text):
    if pd.isna(text):
        return ""
    # Normalisasi teks: lowercase dan hapus karakter khusus
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return text

# Preprocess kolom text untuk pencarian
df['text_processed'] = df['text'].apply(preprocess_text)

# Sidebar untuk filter
st.sidebar.title("🔍 Filter Pencarian")

# Filter berdasarkan rating
st.sidebar.subheader("⭐ Filter Rating")
min_rating, max_rating = st.sidebar.slider(
    "Pilih rentang rating:",
    min_value=1,
    max_value=5,
    value=(1, 5)
)

# Filter berdasarkan sentimen
st.sidebar.subheader("😊 Filter Sentimen")
sentiment_options = ['Semua'] + list(df['sentimen'].unique())
selected_sentiment = st.sidebar.selectbox(
    "Pilih sentimen:",
    sentiment_options
)

# Pencarian teks
st.sidebar.subheader("📝 Pencarian Kata Kunci")
search_query = st.sidebar.text_input("Masukkan kata kunci:")

# Judul aplikasi
st.title("🏖️ Search Engine Pantai Karimunjawa")
st.markdown("Cari informasi pantai di Karimunjawa berdasarkan rating, sentimen, dan kata kunci.")

# Filter data berdasarkan rating
filtered_df = df[(df['stars'] >= min_rating) & (df['stars'] <= max_rating)]

# Filter berdasarkan sentimen
if selected_sentiment != 'Semua':
    filtered_df = filtered_df[filtered_df['sentimen'] == selected_sentiment]

# Filter berdasarkan kata kunci pencarian
if search_query:
    search_lower = search_query.lower()
    # Cari di kolom text yang sudah diproses
    mask = filtered_df['text_processed'].apply(lambda x: search_lower in x)
    filtered_df = filtered_df[mask]

# Tampilkan jumlah hasil
st.subheader(f"📊 Hasil Pencarian: {len(filtered_df)} review ditemukan")

# Tampilkan statistik
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Rating Rata-rata", f"{filtered_df['stars'].mean():.2f} ⭐")
with col2:
    st.metric("Review Positif", f"{len(filtered_df[filtered_df['sentimen'] == 'positive'])}")
with col3:
    st.metric("Review Negatif", f"{len(filtered_df[filtered_df['sentimen'] == 'negative'])}")

# Bagian 1: VISUAL RANK TOP 3
st.markdown("---")
st.subheader("🏆 TOP 3 Pantai Terbaik")

if not filtered_df.empty:
    # Hitung rating rata-rata per pantai
    beach_stats = filtered_df.groupby('title').agg({
        'stars': ['mean', 'count'],
        'sentimen': lambda x: (x == 'positive').sum() / len(x) * 100  # persentase positif
    }).round(2)
    
    # Flatten multi-index columns
    beach_stats.columns = ['rating_mean', 'review_count', 'positive_percentage']
    
    # Hitung skor ranking (rating * persentase positif * log(jumlah review))
    beach_stats['score'] = (
        beach_stats['rating_mean'] * 
        (beach_stats['positive_percentage'] / 100) * 
        np.log1p(beach_stats['review_count'])
    )
    
    # Urutkan berdasarkan skor
    beach_stats = beach_stats.sort_values('score', ascending=False)
    
    # Ambil top 3
    top_3 = beach_stats.head(3)
    
    # Tampilkan visual ranking
    cols = st.columns(3)
    colors = ['#FFD700', '#C0C0C0', '#CD7F32']  # Emas, Perak, Perunggu
    
    for idx, (beach_name, data) in enumerate(top_3.iterrows()):
        with cols[idx]:
            # Tampilkan badge ranking
            st.markdown(f"<div style='text-align: center;'>", unsafe_allow_html=True)
            
            # Badge ranking
            rank_icons = ["🥇", "🥈", "🥉"]
            st.markdown(f"<h2 style='text-align: center;'>{rank_icons[idx]}</h2>", unsafe_allow_html=True)
            
            # Nama pantai
            st.markdown(f"<h3 style='text-align: center; color: {colors[idx]}'>{beach_name}</h3>", unsafe_allow_html=True)
            
            # Rating
            st.metric("⭐ Rating", f"{data['rating_mean']:.2f}")
            
            # Persentase positif
            st.metric("😊 Positif", f"{data['positive_percentage']:.1f}%")
            
            # Jumlah review
            st.metric("📝 Review", f"{int(data['review_count'])}")
            
            st.markdown("</div>", unsafe_allow_html=True)

# Bagian 2: 5 PANTAI REKOMENDASI BERDASARKAN SENTIMEN
st.markdown("---")
st.subheader("👍 5 Pantai Rekomendasi Berdasarkan Sentimen")

# State untuk menyimpan tombol mana yang diklik
if 'show_reviews_for' not in st.session_state:
    st.session_state.show_reviews_for = None

if not filtered_df.empty:
    # Urutkan sentimen: Positive, Neutral, Negative (sesuai permintaan)
    all_sentiments = ['positive', 'neutral', 'negative']
    
    # Buat tab untuk setiap sentimen
    tabs = st.tabs([f"{sent.capitalize()} ({len(filtered_df[filtered_df['sentimen'] == sent])})" 
                    for sent in all_sentiments])
    
    for tab, sentiment in zip(tabs, all_sentiments):
        with tab:
            # Filter data berdasarkan sentimen
            sentiment_df = filtered_df[filtered_df['sentimen'] == sentiment]
            
            if not sentiment_df.empty:
                # Hitung statistik per pantai untuk sentimen ini
                sentiment_beach_stats = sentiment_df.groupby('title').agg({
                    'stars': ['mean', 'count']
                }).round(2)
                sentiment_beach_stats.columns = ['rating_mean', 'review_count']
                
                # Hitung skor (rating * log(jumlah review))
                sentiment_beach_stats['score'] = (
                    sentiment_beach_stats['rating_mean'] * 
                    np.log1p(sentiment_beach_stats['review_count'])
                )
                
                # Urutkan dan ambil top 5
                top_5 = sentiment_beach_stats.sort_values('score', ascending=False).head(5)
                
                # Tampilkan dalam 5 kolom
                cols = st.columns(5)
                
                # Dictionary untuk menyimpan state tombol
                button_keys = {}
                
                for idx, (beach_name, data) in enumerate(top_5.iterrows()):
                    with cols[idx]:
                        # Container dengan tinggi tetap
                        with st.container():
                            # Nama pantai dengan CSS untuk alignment
                            st.markdown(f"""
                                <div style='text-align: center; height: 60px; display: flex; align-items: center; justify-content: center;'>
                                    <strong>{beach_name}</strong>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Rating dengan bintang (rata tengah)
                            stars = "⭐" * int(round(data['rating_mean']))
                            st.markdown(f"""
                                <div style='text-align: center; margin: 10px 0;'>
                                    {stars}<br>
                                    <small>({data['rating_mean']:.1f})</small>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Jumlah review (rata tengah)
                            st.markdown(f"""
                                <div style='text-align: center; margin: 10px 0;'>
                                    📝 {int(data['review_count'])} review
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # Icon ⬇️ untuk melihat review (ditempatkan tengah)
                            button_key = f"{sentiment}_{beach_name}_{idx}"
                            
                            # Container untuk icon dengan margin yang sama
                            col1, col2, col3 = st.columns([1, 2, 1])
                            with col2:
                                # Tombol dengan icon ⬇️ saja
                                if st.button("⬇️", key=button_key, 
                                           use_container_width=True,
                                           help=f"Lihat review untuk {beach_name}"):
                                    # Simpan state tombol yang diklik
                                    st.session_state.show_reviews_for = (beach_name, sentiment)
                
                # Tampilkan tabel review jika ada tombol yang diklik
                if st.session_state.show_reviews_for:
                    selected_beach, selected_sentiment = st.session_state.show_reviews_for
                    
                    # Cek apakah pantai yang dipilih ada dalam top 5 sentimen ini
                    if selected_sentiment == sentiment and selected_beach in top_5.index:
                        st.markdown("---")
                        
                        # Container untuk header dengan tombol close
                        header_col1, header_col2 = st.columns([0.9, 0.1])
                        
                        with header_col1:
                            st.subheader(f"📋 Review untuk {selected_beach} ({selected_sentiment})")
                        
                        with header_col2:
                            # Tombol close dengan icon ✖️
                            if st.button("✖️", key=f"close_{selected_beach}_{sentiment}"):
                                st.session_state.show_reviews_for = None
                                st.rerun()
                        
                        # Ambil review untuk pantai dan sentimen tersebut
                        reviews_df = filtered_df[
                            (filtered_df['title'] == selected_beach) & 
                            (filtered_df['sentimen'] == selected_sentiment)
                        ][['stars', 'text']].head(10)  # Ambil maksimal 10 review
                        
                        if not reviews_df.empty:
                            # Tampilkan tabel review
                            st.dataframe(
                                reviews_df,
                                column_config={
                                    "stars": st.column_config.NumberColumn(
                                        "⭐ Rating",
                                        help="Rating 1-5 bintang",
                                        format="%d ⭐",
                                    ),
                                    "text": st.column_config.TextColumn(
                                        "📝 Review",
                                        help="Isi review",
                                        width="large"
                                    )
                                },
                                use_container_width=True,
                                hide_index=True
                            )
                            
                            # Tampilkan jumlah total review
                            total_reviews = len(filtered_df[
                                (filtered_df['title'] == selected_beach) & 
                                (filtered_df['sentimen'] == selected_sentiment)
                            ])
                            st.caption(f"Menampilkan {len(reviews_df)} dari {total_reviews} review")
                        else:
                            st.info("Tidak ada review untuk pantai ini.")
            else:
                st.info(f"Tidak ada data untuk sentimen {sentiment}")

else:
    st.warning("🚫 Tidak ada data yang sesuai dengan filter pencarian. Coba ubah kriteria filter Anda.")

# Informasi footer
st.markdown("---")
st.markdown("""
**Tips Pencarian:**
- Gunakan slider rating untuk filter bintang ⭐
- Pilih sentimen untuk fokus pada review positif/negatif/neutral
- Masukkan kata kunci seperti "sunset", "bersih", "indah", dll.
""")

# CSS tambahan untuk styling konsisten
st.markdown("""
<style>
    /* Container untuk setiap pantai */
    .stContainer {
        min-height: 250px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    
    /* Tabel review */
    .stDataFrame {
        margin-top: 20px;
        margin-bottom: 20px;
    }
    
    /* Styling untuk tombol icon ⬇️ */
    div.stButton > button {
        background: transparent !important;
        border: 1px solid #ddd !important;
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        min-width: auto !important;
        margin: 5px auto !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 20px !important;
    }
    
    /* Hover effect untuk tombol icon ⬇️ */
    div.stButton > button:hover {
        background: #f0f0f0 !important;
        border-color: #888 !important;
        transform: scale(1.1);
        transition: all 0.2s ease;
    }
    
    /* Styling khusus untuk tombol close */
    div[data-testid="column"]:last-child button {
        background: transparent !important;
        border: none !important;
        color: inherit !important;
        font-size: 20px !important;
        padding: 0 !important;
        margin: 0 !important;
        width: auto !important;
        min-width: auto !important;
        height: auto !important;
        box-shadow: none !important;
    }
    
    /* Hover effect untuk tombol close */
    div[data-testid="column"]:last-child button:hover {
        color: #ff4b4b !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        transform: scale(1.1);
        transition: all 0.2s ease;
    }
    
    /* Align tombol close di kanan atas */
    div[data-testid="column"]:last-child {
        display: flex;
        align-items: flex-start;
        justify-content: flex-end;
        padding-top: 10px;
    }
    
    /* Center align untuk tombol icon ⬇️ */
    div[data-testid="column"]:nth-child(2) {
        display: flex;
        align-items: center;
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)
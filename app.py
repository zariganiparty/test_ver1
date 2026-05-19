import pyroomacoustics as pra
from scipy.io.wavfile import read, write
import numpy as np

from flask import Flask, render_template, request, send_file

import uuid
import os
import glob



# -------------------- flaskゾーン --------------------

app = Flask(__name__)


@app.route("/", methods=["GET","POST"])
def index():

    return render_template("index.html")


@app.route("/simulate", methods=["POST"])
def simulate():

    upload_file = request.files["wavfile"]

    input_filename = f"input_{uuid.uuid4()}.wav"

    upload_file.save(input_filename)

    # wavファイルを読み込む
    fs, signal = read(input_filename)

    #inputしたwavファイルを消す
    os.remove(input_filename)

    # もともとint16っぽいからfloat32に変換してる
    signal = signal.astype(np.float32)


    # 正規化！これがないと爆音ノイズになる
    # signal = signal / np.max(np.abs(signal))    # abs:音データを絶対値に変換 max:最大値を取得

    max_val = np.max(np.abs(signal))
    if max_val >0:
        signal = signal / max_val       #0除算対策


    #部屋
    hh = float(request.form["hh"])
    ho = float(request.form["ho"])
    ht = float(request.form["ht"])

    #マイク
    mh = float(request.form["mh"])
    mo = float(request.form["mo"])
    mt = float(request.form["mt"])

    #音源
    oh = float(request.form["oh"])
    oo = float(request.form["oo"])
    ot = float(request.form["ot"])



    # ----------------------- 部屋の設定 -----------------------



    # 直方体の部屋を作成
    room = pra.ShoeBox(
        [hh, ho, ht],        # 幅　奥行　高さ（m）
        fs = fs,             # サンプリング周波数
        max_order = 3        # 反射回数
    )

    # 音源を部屋に追加
    room.add_source(
        [oh, oo, ot],
        signal = signal
    )

    # マイクを置く
    mic = np.array( [[mh],       # x
                    [mo],       # y
                    [mt]])    # z

    # マイクを部屋に追加
    room.add_microphone_array(mic)



    # ----------------------- シミュレーション -----------------------


    #だんだんたまってくるから今は毎回消す。いつかなんとかする。    
    for file in glob.glob("static/outputs/*.wav"):

        try:
            os.remove(file)

        except:
            pass

    room.simulate()

    # 内部でRIR計算、畳み込み、マイク音生成をしているらしい



    # ------------------------- 結果を保存 ---------------------------



    output = room.mic_array.signals.T.astype(np.float32)
    # float32に変換
   

    max_output = np.max(np.abs(output))

    # 最大値で割る？　→　正規化
    if max_output > 0:
        output = output / max_output

    output_filename = f"output_{uuid.uuid4()}.wav"

    output_path = os.path.join(
        "static",
        "outputs",
        output_filename
    )

    # 結果出力
    write(output_path, room.fs, output)

    # wavはint16かfloat32が一般的？
    # pyroomabosticはfloat64で返すらしい？


    


    return render_template(
        "result.html",
        filename=output_filename
    )






# ----------------------------------------------------------------

# print(fs)
# print(signal.shape)
# print(signal.dtype)

# シミュレーションしたり加工したり？だからwavファイルはint16よりfloat32のほうがいいかも


# 2026/05/08　次はflaskと連携させる or 直方体以外の部屋 or 3D可視化 or 材料追加

# room.compute_rir()

# rir = room.rir[0][0]

# print(rir) nanikore

# https://chatgpt.com/c/69fd986f-5930-8320-99e3-a6821067cc14


if __name__ == "__main__":
    app.run(debug=True)
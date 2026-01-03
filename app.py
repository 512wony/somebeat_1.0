from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'somesecret'

# =========================
# 테스트용 데이터
# =========================
users = {'nickname': '테스트', 'password': '3333', 'gender': '여', 'table': 'T1', 'bit': 1,
                'received_som': [], 'new_received_som': [], 'checked_som_once': False, 'last_checked_som_count': 0}

HOST_ACCOUNT = {
    'nickname': 'host_ysj',
    'password': 'host',
    'bit_given': 0
}

STAFF_NICKNAME = "staff_sb"
STAFF_PASSWORD = "staff123"

orders = []

menu_status = {
    "닭강정": True,
    "카나페": True,
    "팝콘": True,
    "붕어빵(10시 이후)": True,
    "나쵸(2부)": True,
    "과일(2부)": True,
    "두부김치": True,
    "타코야키": True
}

# =========================
# 회원가입
# =========================
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        nickname = request.form['nickname']
        password = request.form['password']
        table = request.form['table']
        gender = request.form['gender']

        if nickname in users:
            flash("이미 존재하는 닉네임입니다!", category="signup")
            return render_template('signup.html')

        users[nickname] = {
            'nickname': nickname,
            'password': password,
            'gender': gender,
            'table': table,
            'bit': 1,
            'received_som': [],
            'new_received_som': [], 
            'checked_som_once': False,
            'last_checked_som_count': 0
        }

        session['nickname'] = nickname
        session['is_host'] = False
        return redirect(url_for('main'))

    return render_template('signup.html')


# =========================
# 로그인
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nickname = request.form['nickname']
        password = request.form['password']

        # 스태프 로그인
        if nickname == STAFF_NICKNAME and password == STAFF_PASSWORD:
            session.clear()
            session['nickname'] = STAFF_NICKNAME
            session['role'] = 'staff'
            return redirect(url_for('order'))

        # 호스트 로그인
        if nickname == HOST_ACCOUNT['nickname'] and password == HOST_ACCOUNT['password']:
            session.clear()
            session['nickname'] = nickname
            session['is_host'] = True
            session['role'] = 'host' 
            return redirect(url_for('host'))

        # 일반 유저 로그인
        if nickname in users and users[nickname]['password'] == password:
            session.clear()
            session['nickname'] = nickname
            session['is_host'] = False
            session['role'] = 'user' 
            return redirect(url_for('main'))

        flash("아이디 또는 비밀번호가 틀렸습니다!", category="login")

    return render_template('login.html')


# =========================
# 메인 페이지
# =========================
@app.route('/', methods=['GET', 'POST'])
def main():
    nickname = session.get('nickname')

    if not nickname or session.get('is_host'):
        return redirect(url_for('login'))

    user = users.get(nickname)

    if not user:
        return redirect(url_for('login'))

    total_som = (
        len(user.get('received_som', [])) +
        len(user.get('new_received_som', []))
    )

    received_count = (
        len(user.get('received_som', [])) +
        len(user.get('new_received_som', []))
    )    
    search_result = None

    if request.method == 'POST':

        # 썸 보내기
        if 'send_som' in request.form:
            target_nick = request.form['send_som']

            if user['bit'] < 1:
                flash("비트가 부족합니다! 💔")

            elif target_nick not in users:
                flash("해당 닉네임을 찾을 수 없습니다!")

            else:
                user['bit'] -= 1
                users[target_nick]['new_received_som'].append(nickname)
                flash(f"{target_nick}에게 썸을 보냈습니다! 💕")

            search_result = users.get(target_nick)

        # 닉네임 검색
        elif 'search_nick' in request.form:
            nick = request.form['search_nick'].strip()

            if nick and nick in users:
                search_result = users[nick]
            else:
                search_result = False   

        # 받은 썸 확인
        elif 'check_som' in request.form:

            # 새로 받은 썸이 없으면
            if not user['new_received_som']:
                flash("새로 받은 썸이 없어요 💭")

            # 처음 공개 (2비트 차감)
            elif not user['checked_som_once']:
                if user['bit'] >= 2:
                    user['bit'] -= 2
                    user['received_som'].extend(user['new_received_som'])
                    user['new_received_som'] = []
                    user['checked_som_once'] = True
                    flash("모든 썸 확인 완료! 💕 (2비트 차감)")
                else:
                    flash("비트가 부족합니다! 💔")

            # 이미 공개 + 추가 썸 있음 (무료)
            else:
                user['received_som'].extend(user['new_received_som'])
                user['new_received_som'] = []
                flash("추가로 받은 썸을 확인했어요 💕")


    received_som_list = user['received_som'] if user['checked_som_once'] else []

    return render_template(
        'main.html',
        user=user,
        received_count=received_count, 
        total_som=total_som,
        search_result=search_result, 
        received_som_list=received_som_list,
        is_host=session.get('is_host', False)
    )


# =========================
# 초기화
# =========================
@app.route('/host/reset', methods=['POST'])
def host_reset():
    if not session.get('is_host'):
        return redirect(url_for('login'))

    # users 초기화 → 모든 참가자 삭제
    global users
    users = {}

    # orders 초기화
    global orders
    orders = []

    # 호스트 비트 초기화
    HOST_ACCOUNT['bit_given'] = 0

    flash("서버가 완전히 초기화되었습니다! ✅")
    return redirect(url_for('host'))
    
# =========================
# 호스트 페이지
# =========================
@app.route('/host', methods=['GET', 'POST'])
def host():
    if not session.get('is_host'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'give_bit' in request.form:
            for u in users.values():
                u['bit'] += 1
            HOST_ACCOUNT['bit_given'] += 1
            flash(f"호스트가 총 {HOST_ACCOUNT['bit_given']}개의 비트를 선물했습니다!", category="host")

    return render_template('host.html', users=users, host=HOST_ACCOUNT, menu_status=menu_status)


@app.route('/host/toggle_menu', methods=['POST'])
def toggle_menu():
    if not session.get('is_host'):
        return redirect(url_for('login'))

    menu = request.form.get('menu')
    if menu in menu_status:
        menu_status[menu] = not menu_status[menu]

    return redirect(url_for('host'))


# =========================
# 주문 페이지
# =========================
@app.route('/order', methods=['GET', 'POST'])
def order():
    nickname = session.get('nickname')
    if not nickname:
        return redirect(url_for('login'))

    is_host = session.get('is_host', False)
    user = HOST_ACCOUNT if is_host else users.get(nickname)

    menu_list = ["닭강정", "카나페", "팝콘", "붕어빵(10시 이후)", "나쵸(2부)", "과일(2부)", "두부김치", "타코야키"]
    tables = [f"T{i}" for i in range(1, 9)]

    if request.method == 'POST':

        # 주문 추가
        if 'table' in request.form and 'menu' in request.form:
            table = request.form['table']
            menu = request.form['menu']
            quantity = int(request.form['quantity'])

            orders.append({
                'id': len(orders),
                'table': table,
                'menu': menu,
                'quantity': quantity,
                'status': '조리중'
            })

            flash("주문 완료!", category="order")
            return redirect(url_for('order'))

        # 배달 완료 처리
        elif 'deliver_id' in request.form:
            deliver_id = int(request.form['deliver_id'])
            for o in orders:
                if o['id'] == deliver_id:
                    o['status'] = '배달완료'
                    flash(f"{o['menu']} 배달 완료!")
                    break
            return redirect(url_for('order'))

    return render_template(
        'order.html',
        user=user,
        orders=orders,
        menu_list=menu_list,
        menu_status=menu_status,
        tables=tables,
        is_host=is_host
    )


# =========================
# 로그아웃
# =========================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run()



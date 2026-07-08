// ==============================
// Biến lưu nhân viên được chọn
// ==============================

let selectedEmployee = "";

// ==============================
// Biến lưu mã PIN
// ==============================

let pin = "";

// ==============================
// Chọn nhân viên
// ==============================

function selectEmployee(card){

    // Bỏ màu xanh của tất cả card
    document.querySelectorAll(".employee-card").forEach(function(item){

        item.classList.remove("active");

    });

    // Thêm màu xanh cho card vừa chọn
    card.classList.add("active");

    // Lưu userID
    selectedEmployee = card.dataset.userid;

    console.log("Employee:", selectedEmployee);

}

// ==============================
// Nhấn số
// ==============================

function pressNumber(number){

    if(pin.length >= 4){

        return;

    }

    pin += number;

    updatePinDisplay();

}

// ==============================
// Xóa PIN
// ==============================

function deletePin(){

    pin = pin.slice(0,-1);

    updatePinDisplay();

}

// ==============================
// Hiển thị PIN
// ==============================

function updatePinDisplay(){

    const dots = document.querySelectorAll(".pin-display span");

    dots.forEach(function(dot,index){

        if(index < pin.length){

            dot.innerHTML = "●";

        }

        else{

            dot.innerHTML = "○";

        }

    });

}

// ==============================
// Login
// ==============================

async function login(){

    if(selectedEmployee==""){

        alert("Please select an employee.");

        return;

    }

    if(pin.length!=4){

        alert("PIN must have 4 digits.");

        return;

    }

    const response = await fetch("/login",{

        method:"POST",

        headers:{

            "Content-Type":"application/json"

        },

        body:JSON.stringify({

            userID:selectedEmployee,

            pin:pin

        })

    });

    const result = await response.json();

    if(result.success){

        if(result.position === "Admin"){

            window.location.href = "/admin/dashboard";

        }

        else if(result.position === "Waiter"){

            window.location.href = "/waiter/dashboard";

        }

        else if(result.position === "Kitchen Staff"){

            window.location.href = "/kitchen/dashboard";

        }

        else if(result.position === "Cashier"){

            window.location.href = "/cashier/invoice";

        }

        else{

            alert("Unknown role.");

        }

    }

    else{

        alert(result.message);

    }

}
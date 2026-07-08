-- ==========================================
-- CREATE DATABASE
-- ==========================================
CREATE DATABASE RestaurantManagement;
GO

USE RestaurantManagement;
GO

-- ==========================================
-- Employee
-- ==========================================
CREATE TABLE Employee
(
    userID CHAR(3) PRIMARY KEY,
    fullName VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    position VARCHAR(50) NOT NULL,
    isActive BIT DEFAULT 1,
    pin VARCHAR(10) NOT NULL
);

-- ==========================================
-- Table
-- ==========================================
CREATE TABLE RestaurantTable
(
    tableNumber INT PRIMARY KEY,
    status VARCHAR(30) NOT NULL
);

-- ==========================================
-- Category
-- ==========================================
CREATE TABLE Category
(
    categoryID CHAR(6) PRIMARY KEY,
    categoryName VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    status VARCHAR(30)
);

-- ==========================================
-- Dish
-- ==========================================
CREATE TABLE Dish
(
    dishID CHAR(6) PRIMARY KEY,
    categoryID CHAR(6) NOT NULL,
    name VARCHAR(100) NOT NULL,
    image VARCHAR(255),
    description VARCHAR(MAX),
    ingredients VARCHAR(MAX),
    price DECIMAL(10,2) NOT NULL,
    isAvailable BIT DEFAULT 1,

    CONSTRAINT FK_Dish_Category
        FOREIGN KEY(categoryID)
        REFERENCES Category(categoryID)
);

-- ==========================================
-- Orders
-- ==========================================
CREATE TABLE Orders
(
    orderID CHAR(6) PRIMARY KEY,
    tableNumber INT NOT NULL,
    status VARCHAR(30),
    orderDate DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_Order_Table
        FOREIGN KEY(tableNumber)
        REFERENCES RestaurantTable(tableNumber)
);

-- ==========================================
-- OrderDetail
-- ==========================================
CREATE TABLE OrderDetail
(
    orderID CHAR(6),
    dishID CHAR(6),
    quantity INT NOT NULL,
    specialNote VARCHAR(255),

    PRIMARY KEY(orderID,dishID),

    CONSTRAINT FK_OrderDetail_Order
        FOREIGN KEY(orderID)
        REFERENCES Orders(orderID),

    CONSTRAINT FK_OrderDetail_Dish
        FOREIGN KEY(dishID)
        REFERENCES Dish(dishID)
);

-- ==========================================
-- Invoice
-- ==========================================
CREATE TABLE Invoice
(
    invoiceID CHAR(6) PRIMARY KEY,
    orderID CHAR(6) UNIQUE,
    tax DECIMAL(10,2),
    finalAmount DECIMAL(10,2),
    createdAt DATETIME DEFAULT GETDATE(),

    CONSTRAINT FK_Invoice_Order
        FOREIGN KEY(orderID)
        REFERENCES Orders(orderID)
);

-- ==========================================
-- Payment
-- ==========================================
CREATE TABLE Payment
(
    paymentID CHAR(6) PRIMARY KEY,
    invoiceID CHAR(6) UNIQUE,
    paymentMethod NVARCHAR(50),
    amount DECIMAL(10,2),
    paymentTime DATETIME,
    cashierID CHAR(3),

    CONSTRAINT FK_Payment_Invoice
        FOREIGN KEY(invoiceID)
        REFERENCES Invoice(invoiceID),

    CONSTRAINT FK_Payment_Cashier
        FOREIGN KEY(cashierID)
        REFERENCES Employee(userID)
);

-- ==========================================
-- OrderHistory
-- ==========================================
CREATE TABLE OrderHistory
(
    historyID CHAR(6) PRIMARY KEY,
    orderID CHAR(6),
    changedBy CHAR(3),
    [timestamp] DATETIME DEFAULT GETDATE(),
    changeDetails NVARCHAR(MAX),

    CONSTRAINT FK_OrderHistory_Order
        FOREIGN KEY(orderID)
        REFERENCES Orders(orderID),

    CONSTRAINT FK_OrderHistory_Employee
        FOREIGN KEY(changedBy)
        REFERENCES Employee(userID)
);

-- ==========================================
-- AuditLog
-- ==========================================
CREATE TABLE AuditLog
(
    logID CHAR(6) PRIMARY KEY,
    userID CHAR(3),
    action VARCHAR(100),
    [timestamp] DATETIME DEFAULT GETDATE(),
    details VARCHAR(MAX),

    CONSTRAINT FK_AuditLog_Employee
        FOREIGN KEY(userID)
        REFERENCES Employee(userID)
);

-- ==========================================
-- RevenueReport
-- ==========================================
CREATE TABLE RevenueReport
(
    reportID CHAR(6) PRIMARY KEY,
    fromDate DATETIME,
    toDate DATETIME,
    totalRevenue DECIMAL(18,2)
);


USE RestaurantManagement;
GO

DROP TABLE IF EXISTS AuditLog;
DROP TABLE IF EXISTS OrderHistory;
DROP TABLE IF EXISTS Payment;
DROP TABLE IF EXISTS Invoice;
DROP TABLE IF EXISTS OrderDetail;
DROP TABLE IF EXISTS Orders;
DROP TABLE IF EXISTS Dish;
DROP TABLE IF EXISTS Category;
DROP TABLE IF EXISTS RestaurantTable;
DROP TABLE IF EXISTS RevenueReport;
DROP TABLE IF EXISTS Employee;
GO


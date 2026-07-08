USE RestaurantManagement;

-- ==========================
-- Employee
-- ==========================
INSERT INTO Employee(userID, fullName, phone, position, isActive, pin)
VALUES
('E01','John Smith','0901111111','Admin',1,'1234'),
('E02','Emily Johnson','0901111112','Waiter',1,'1111'),
('E03','Michael Brown','0901111113','Waiter',1,'2222'),
('E04','David Wilson','0901111114','Kitchen Staff',1,'3333'),
('E05','Sarah Miller','0901111115','Kitchen Staff',1,'4444'),
('E06','James Taylor','0901111116','Cashier',1,'5555');
GO

-- ==========================
-- Restaurant Table
-- ==========================
INSERT INTO RestaurantTable(tableNumber,status)
VALUES
(1,'Available'),
(2,'Occupied'),
(3,'Occupied'),
(4,'Occupied'),
(5,'Occupied'),
(6,'Available'),
(7,'Occupied'),
(8,'Available'),
(9,'Occupied'),
(10,'Occupied'),
(11,'Occupied'),
(12,'Available');
GO

-- ==========================
-- Category
-- ==========================
INSERT INTO Category(categoryID,categoryName,description,status)
VALUES
('CATE01','Appetizer','Starter dishes','Active'),
('CATE02','Main Course','Main dishes','Active'),
('CATE03','Dessert','Desserts','Active'),
('CATE04','Drink','Beverages','Active');
GO

-- ==========================
-- Dish
-- ==========================
INSERT INTO Dish(dishID,categoryID,name,image,description,ingredients,price,isAvailable)
VALUES
('DISH01','CATE01','French Fries','images/fries.png','Crispy potato fries','Potato, Salt, Oil',45000,1),
('DISH02','CATE01','Spring Rolls','images/spring_roll.png','Vietnamese spring rolls','Rice Paper, Pork, Shrimp',55000,1),
('DISH03','CATE02','Fried Rice','images/fried_rice.png','Egg fried rice','Rice, Egg, Carrot, Peas',65000,1),
('DISH04','CATE02','Beef Steak','images/steak.png','Australian beef steak','Beef, Butter, Black Pepper',250000,1),
('DISH05','CATE02','Seafood Pasta','images/pasta.png','Creamy seafood pasta','Pasta, Shrimp, Squid, Cream',180000,1),
('DISH06','CATE02','Pizza Margherita','images/pizza.png','Classic Italian pizza','Pizza Dough, Tomato Sauce, Mozzarella',170000,1),
('DISH07','CATE03','Cheesecake','images/cheesecake.png','New York cheesecake','Cream Cheese, Butter, Sugar',70000,1),
('DISH08','CATE03','Ice Cream','images/icecream.png','Vanilla ice cream','Milk, Vanilla',45000,1),
('DISH09','CATE04','Coca Cola','images/coke.png','330ml','Coca Cola',25000,1),
('DISH10','CATE04','Orange Juice','images/orange_juice.png','Fresh orange juice','Orange',50000,1);
GO

-- ==========================
-- Orders
-- ==========================
INSERT INTO Orders(orderID, tableNumber, status, orderDate)
VALUES
('ORD001',2,'Preparing','2026-07-08 10:00:00'),
('ORD002',3,'Pending','2026-07-08 10:05:00'),
('ORD003',4,'Ready','2026-07-08 10:10:00'),
('ORD004',5,'Preparing','2026-07-08 10:15:00'),
('ORD005',7,'Pending','2026-07-08 10:20:00'),
('ORD006',9,'Ready','2026-07-08 10:25:00'),
('ORD007',10,'Preparing','2026-07-08 10:30:00'),
('ORD008',11,'Ready','2026-07-08 10:35:00'),
('ORD009',1,'Completed','2026-07-08 09:30:00'),
('ORD010',6,'Completed','2026-07-08 09:45:00');
GO

-- ==========================
-- Order Detail
-- ==========================
INSERT INTO OrderDetail(orderID,dishID,quantity,specialNote)
VALUES

('ORD001','DISH03',2,'Less salt'),
('ORD001','DISH09',2,'No ice'),

('ORD002','DISH04',1,'Medium rare'),
('ORD002','DISH10',2,'Less sugar'),

('ORD003','DISH06',1,NULL),
('ORD003','DISH09',3,NULL),

('ORD004','DISH05',2,NULL),
('ORD004','DISH08',2,NULL),

('ORD005','DISH02',3,'Extra sauce'),
('ORD005','DISH07',2,NULL),

('ORD006','DISH04',2,NULL),
('ORD006','DISH10',2,NULL),

('ORD007','DISH03',3,'No egg'),
('ORD007','DISH09',3,NULL),

('ORD008','DISH01',2,NULL),
('ORD008','DISH06',1,'Extra cheese'),

('ORD009','DISH05',1,NULL),
('ORD009','DISH09',2,NULL),

('ORD010','DISH04',1,'Well done'),
('ORD010','DISH08',2,NULL);
GO

-- ==========================
-- Invoice
-- ==========================
INSERT INTO Invoice(invoiceID,orderID,tax,finalAmount,createdAt)
VALUES

('INV001','ORD003',19600,264600,'2026-07-08 10:40:00'),

('INV002','ORD006',48000,648000,'2026-07-08 10:45:00'),

('INV003','ORD008',17200,232200,'2026-07-08 10:50:00'),

('INV004','ORD009',18400,248400,'2026-07-08 09:40:00'),

('INV005','ORD010',27200,367200,'2026-07-08 09:55:00');
GO

-- ==========================
-- Payment
-- ==========================
INSERT INTO Payment
(paymentID,invoiceID,paymentMethod,amount,paymentTime,cashierID)
VALUES

('PAY001','INV004','Cash',248400,'2026-07-08 09:45:00','E06'),

('PAY002','INV005','Bank Transfer',367200,'2026-07-08 10:00:00','E06');
GO

-- ==========================
-- Revenue Report
-- ==========================
INSERT INTO RevenueReport
(reportID,fromDate,toDate,totalRevenue)
VALUES
('RPT001',
'2026-07-08 00:00:00',
'2026-07-08 23:59:59',
615600);
GO

DELETE FROM Payment;
DELETE FROM Invoice;
DELETE FROM OrderDetail;
DELETE FROM Orders;
DELETE FROM RevenueReport;
DELETE FROM Dish;
DELETE FROM Category;
DELETE FROM RestaurantTable;
DELETE FROM Employee;

SELECT * FROM Employee;
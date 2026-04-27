-- Seed sample line items linked to seeded orders.
-- Each line ties an order to a product, quantity, and unit sell price.
INSERT INTO OrderItems (`OrderID`, `ProductID`, `quantity`, `price`) VALUES
(1, 1, 1, 103.00),
(1, 3, 2, 100.00),
(2, 2, 1, 300.00),
(2, 4, 1, 110.00),
(3, 5, 3, 30.00);
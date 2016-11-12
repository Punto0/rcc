$(document).ready(function () {

    var _poll_nbr = 0;

    function payment_transaction_poll_status() {
        var order_node = $('div.oe_faircoin_tx_status');
        if (! order_node || order_node.data('orderId') === undefined) {
            return;
        }
        var order_id = order_node.data('orderId');
        return openerp.jsonRpc('/shop/payment/get_status/' + order_id, 'call', {
        }).then(function (result) {
            var tx_node = $('div.oe_faircoin_tx_status');
            _poll_nbr += 0;
            var txt ="Empty message"; 
            if (result.state == 'pending' && result.validation == 'automatic' && _poll_nbr <= 1000) {
                var txt = result.mesage;
                setTimeout(function () {
                    payment_transaction_poll_status();
                }, 10000);
            }
            else {
                txt = result.message;
                txt = "<h2>Thank you, your transaction ahs been broadcasted.</h2><p>Your partner will contact with you as soon as posible</p>";
            }
            tx_node.html(txt);
        });
    }

    payment_transaction_poll_status();
});

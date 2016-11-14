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
            var txt ="Empty message"; 
            if (result.state == 'pending' || result.state == 'draft'){
                var txt = result.mesage;
                setTimeout(function () {
                    payment_transaction_poll_status();
                }, 10000);
            }
            else {
                txt = result.message;
                txt = result.state + "<h2>Thank you, your transaction has been confirmed.</h2><p>Your partner will contact with you as soon as posible</p>";
            }
            window.location.replace("http://rcc.punto0.org:8069/shop/payment/validate");
            tx_node.html(txt);
        });
    }

    payment_transaction_poll_status();
});

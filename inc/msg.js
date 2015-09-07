var MsgMap = {
	'SetNodeName': ['warning', '当前节点须设定节点名', 'zzzzzzzz'],
	'SetUserName': ['error', '当前用户须设定用户名', 'eeeeeeeee'],
}

var PFMessage = function( Type, obj )
{
	var msg = this;

	this.Type = Type;
	this.Obj = obj;
	this.Level = MsgMap[Type][0];

	this.Notice = function( dom )
	{
		dom.html( '<span class="infotype">' + MsgMap[this.Type][0] + '</span>' + MsgMap[this.Type][1] );
		dom.click( function()
		{
			alert( MsgMap[msg.Type][2] );
		} );
	}
}
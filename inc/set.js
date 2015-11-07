var SetItem = function( name, tbody, setFunc )
{
	var item = this;

	var NameMap = {
			'CurNode': ['本地节点', 'localnode'],
			'CurUser': ['本地用户', 'localuser'],
					};

	this.Draw = function()
	{
		var Choice = $( '<div class="choice" id="' + NameMap[name][1] + '"><div class="title"><span class="trigger">◣</span>'
					 + NameMap[name][0] + '</div><div class="content"><table></table>'
					 + '<br><button>提交</button></div></div>' );

		$( 'tr.scalable>td', tbody ).append( '<span class="add">+</span>' );

		$( 'table', Choice ).html( tbody );
		$( '.content', Choice ).hide();

		$( 'span.add', Choice ).click( function()
		{
			$( this ).before( '<input type="text"/><br>' );
		} );

		Choice.children( '.title' ).click( function()
		{
			var Others = Choice.siblings( '.choice' );
			Others.children( '.content' ).hide( 200 );
			Others.children( '.title' ).children( '.trigger' ).html( '◣' );
			$( this ).children( '.trigger' ).html( '◤' );
			Choice.children( '.content' ).show( 300 );
		} );

		$( 'button', Choice ).click( function()
		{
			setFunc( $( 'tbody', Choice ));
		} );

		$( '#setpg' ).append( Choice );
	};

	this.Draw();

};


var Manager = function( owner )
{
	var manager = this;
	this.Owner = owner;

	
}
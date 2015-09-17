var Forum = function( owner )
{
	var frm = this;

	this.Owner = owner;
	this.StartPos = 0;
	this.ListLabel = '';
	this.SortCol = 'LastTime';
	this.TopicObj = {};


	this.Init = function()
	{
		$( '#newtpcbtn' ).click( function()
		{
			//alert( 'ssssss' );
			$( '#tpcinput' ).toggle( 350 );
		} );

		$( '.tpctd>button' ).click( function()
		{
			//console.log( 'newtopic' );
			var Content = $( '.tpctd>textarea' ).val()
			if( Content.length < 20 )
			{
				$( '.tpctd>.note' ).html( '帖子内容不能少于 20 字。' );
				return;
			}

			var AtclLabels = $( '.tpctd>:text' ).val()

			//console.log( AtclLabels );
			if( !AtclLabels )
			{
				$( '.tpctd>.note' ).html( '标签不能为空。' );
				return;
			}

			$( '.tpctd>.note' ).html( '' );

			var TopicData = {
				'cmd': 'NewTopic',
				'content': Content,
				'Labels': AtclLabels,
				'life': 86400000 * $( '.tpctd>select' ).children( 'option:selected' ).val(),
			};

			console.log( TopicData );

			frm.Owner.Post( TopicData, 'GetResult' );
		} );

		$( '#firstth' ).click( function()
		{
			frm.SortCol = 'FirstTime';
			frm.StartPos = 0;
			$( '#lastth>span' ).prependTo( $( this ));

			frm.GetNextPage();
		} );

		$( '#lastth' ).click( function()
		{
			frm.SortCol = 'LastTime';
			frm.StartPos = 0;
			$( '#firstth>span' ).prependTo( $( this ));

			frm.GetNextPage();
		} );

		$( '#returntolist' ).click( function()
		{
			$( '#atclpg' ).hide( 200 );
			$( '#listpg' ).show( 300 );
		} );
	};

	this.SetClickTitle = function( dom )
	{
		$( 'span.title', dom ).click( function()
		{
			var Root = $( this ).closest( 'tr' ).data( 'root' );
			//console.log( Root );
			frm.Owner.Post( { cmd: 'GetAtclTree', root: Root }, 'GetResult' );
		} );
	};

	this.SetClickLastTime = function( dom )
	{

	};
	
	this.SetClickArrow = function( dom )
	{

	};

	this.SetAttr = function( dom )
	{
		this.SetClickTitle( dom );
		this.SetClickLastTime( dom );
		this.SetClickArrow( dom );

		setTimeout( function(){ dom.removeClass( 'new' ); }, 2000 );
	};
	
	this.ShowContent = function( c )
	{
		return c.replace( /\&/g, '&amp;' ).replace( /\>/g, '&gt;' ).replace( /\</g, '&lt;' ).replace( /\n/g, '<br/>' );
	};

	this.ShowAtcls = function( treeData )
	{
		$( '#atclarea' ).html( '' );
		
		var Tree = this.TopicObj[treeData[0]] = _( treeData[1] ).omit( function( v )
		{
			return v[0].Type == 1;
			/*if( v[0].Type == 1 )
			{
				console.log( k, v[0].ParentID ); 
				var Parent = treeData[1][v[0].ParentID];

				Parent[0].Liked = Parent[0].Liked || [];
				Parent[0].Liked.push( v[0].AuthPubKey );
				console.log( Parent[0].Liked )
				return true;
			}
			return false;*/
		} );

		//console.log( Tree );

		_( Tree ).chain().pairs().sortBy( function( p )
		{
			return p[1][0].CreateTime;
		} ).each( function( p )
		{
			console.log( p );
			var AtclDiv = $( '<div class="atcl" id="Atcl_' + p[0] + '"><table><tbody><tr> \
				<td class="atclleft"><div class="nickname"></div> \
				<div class="randomart" title="不同用户可能有相同的用户名，\n可通过 RandomArt 识别用户。"></div> \
				<div class="manageuser"></div></td><td class="atclright"><div class="atcltop"> \
				<span class="time"></span><span class="atclid"></span><span class="lineright"> \
				<span class="bigger" title="放大帖子正文">大</span><span class="smaller" title="缩小帖子正文">小</span> \
				</span></div><div class="atclbody"></div> \
				<div class="atclfoot"><span class="manage">zzzzzzzzzzzzz</span><span class="lineright"> \
				<!--button class="like">赞<span class="likenum"></span></button--> \
				<button class="reply">回复</button></span></div> \
				</td></tr></tbody></table><div></div></div>' );

			var AuthPubKey = p[1][0].AuthPubKey;
			var AuthStatus = frm.Owner.ChkAuthStatus( AuthPubKey );
			var NameDiv = $( '.nickname', AtclDiv );

			NameDiv.html( p[1][0].NickName );
			NameDiv.attr( 'title', '用户公钥：' + AuthPubKey );

			if( AuthStatus >= 0 )
			{
				$( '.atclbody', AtclDiv ).html( frm.ShowContent( p[1][1] ));
			}
			else
			{
				$( '.atclbody', AtclDiv ).html( '因用户被屏蔽内容不可见。<button>点此查看</button>' );
				$( '.atclbody>button', AtclDiv ).click( function()
				{
					$( this ).parent().html( frm.ShowContent( p[1][1] ));
				} );
			}
			
			$( '.randomart', AtclDiv ).html( frm.RandomArt( str_md5( AuthPubKey )));
			$( '.manageuser', AtclDiv ).append( AuthStatus >= 0 ? '<button class="blockbtn">屏蔽</button>' : '<button class="unblockbtn">解除屏蔽</button>' );
			$( '.manageuser', AtclDiv ).append( AuthStatus <= 0 ? '<button class="followbtn">关注</button>' : '<button class="unfollowbtn">取消关注</button>' );
			$( '.time', AtclDiv ).html( frm.ShowTime( p[1][0].CreateTime ));
			$( '.atclid', AtclDiv ).html( '&nbsp;' + p[0] );
			//$( '.likenum', AtclDiv ).html(( p[1][0].Liked || [] ).length );
			$( '.atclfoot', AtclDiv ).data( 'atclid', p[0] );

			$( '#atclarea' ).append( AtclDiv );
		} );

		$( '.atcltop>.lineright>span' ).click( function()
		{
			var Body = $( this ).closest( 'td' ).children( '.atclbody' );
			var size = parseFloat( Body.css( "font-size" ), 10 );
			var diff = $( this ).hasClass( 'bigger' ) ? 2: -2;
			size += diff;
			Body.css( "font-size", size + 'px' );
			Body.css( "line-height", size * 1.5 + "px" );				
		} );

		$( '.reply' ).click( function()
		{
			var TBody = $( this ).closest( 'tbody' );
			if( TBody.children( 'tr.input' ).length > 0 )
			{
				TBody.children( 'tr.input' ).toggle( 300 );
				return;
			}
			var TR = $( '<tr class="input"></tr>' );
			TR.html( $( '#tpcinput tr' ).html());
			$( 'select', TR ).remove();
			$( ':text', TR ).remove();
			$( 'button', TR ).html( '回复' );
			TR.hide();

			TBody.append( TR );
			TR.show( 400 );
		} );

		/*$( '.like' ).click( function()
		{
			//console.log( Tree );
			var AuthPubK = frm.Owner.CurUser[0];
			var AtclId = $( this ).closest( '.atclfoot' ).data( 'atclid' );
			var Atcl = Tree[AtclId]

			//console.log( AuthPubK, Atcl );
			if( AuthPubK == Atcl[0].AuthPubKey )
			{
				alert( '不能给自己的帖子点赞。' );
				return;
			}
			if( _( Atcl[0].Liked ).contains( AuthPubK ))
			{
				alert( '不能重复点赞。' );
				return;
			}

			frm.Owner.Post( { cmd: 'Like', atclId: AtclId, root: treeData[0] }, 'GetResult' );
		} );*/
	};

	/*this.AddLike = function( newLike )
	{
		var ParentId = 'Atcl_' + newLike[0].ParentID;
		var LikeNum = $( '#' + ParentId + ' .likenum' );
		LikeNum.html( Number( LikeNum.html()) + 1 );
	};*/

	this.RandomArt = function( data )
	{
		var Bound = [
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
				[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
					];

		var x = 8;
		var y = 4;

		Bound[y][x] = -1;

		_( data ).each( function( c )
		{
			var Byte = c.charCodeAt();
			for( var i = 0; i < 4; i++ )
			{
				if( Byte & 0x01 && x < 16 )
				{
					x++;
				}
				else if( !( Byte & 0x01 ) && x > 0 )
				{
					x--;
				}

				if( Byte & 0x02 && y < 8 )
				{
					y++;
				}
				else if( !( Byte & 0x02 ) && y > 0 )
				{
					y--;
				}

				if( Bound[y][x] >= 0 )
				{
					Bound[y][x]++;
				}
				
				Byte >>= 2;
			}
		} );

		Bound[y][x] = -2;

		var s = '';
		_( Bound ).each( function( ln )
		{
			_( ln ).each( function( n )
			{
				s += n >= 0 ? ' .o+=*BOX@%&#/^ES'[n] : 'ES'[n + 2];
			} );
			s += '<br/>'
		} );

		return s.replace( / /g, '&nbsp;' );
	};

	this.GetNextPage = function()
	{
		var Param = {
			'cmd': 'GetTpcList',
			'start': this.StartPos,
			'label': this.ListLabel,
			'sortby': this.SortCol,
					};
		//console.log( Param );

		if( this.StartPos == 0 )
		{
			$( '#tpclist>table>tbody>tr:gt(0)' ).remove();
		}

		frm.Owner.Post( Param, 'GetResult' );
	};

	this.FillZero = function( s )
	{
		return ( '00' + s ).slice( -2 );
	};

	this.ShowTime = function( intTime, onlyDate )
	{
		var d = new Date();
		d.setTime( intTime );
		if( onlyDate )
		{
			return d.getFullYear() + '-' + this.FillZero( d.getMonth() + 1 ) + '-' + this.FillZero( d.getDate());
		}
		return d.getFullYear() + '-' + this.FillZero( d.getMonth() + 1 ) + '-' + this.FillZero( d.getDate()) + ' '
				+ this.FillZero( d.getHours()) + ':' + this.FillZero( d.getMinutes()) + ':' + this.FillZero( d.getSeconds());
	};

	this.TopicTR = function( tpcdata )
	{
		var TR = $( '<tr class="new" title="展开话题"><td class="title" title="进入话题"></td> \
			<td class="first"></td><td class="num">1</td><td class="last" title="查看更新"></td></tr>' );
		var LabelSpans = _( tpcdata[2].split( ',' )).chain().map( function( lb )
			{
				return '<span class="tpclabel">' + lb + '</span>';
			} ).value().join( '' );
		//console.log( LabelSpans );
		var Title = '<span class="arrow">◣</span><span class="title">' + tpcdata[1] + '</span>' + LabelSpans;
		TR.children( 'td:eq(0)' ).html( Title )
		TR.children( 'td:eq(1)' ).html( tpcdata[5] + '<br><span class="firsttime">' + this.ShowTime( tpcdata[6], true ) + '</span>' );
		TR.children( 'td:eq(2)' ).html( tpcdata[4] )
		TR.children( 'td:eq(3)' ).html( '<span class="lasttime">' + this.ShowTime( tpcdata[8] ) + '</span><br>' + tpcdata[7] );
		TR.data( 'root', tpcdata[0] );

		return TR;
	};

	this.Init();
}